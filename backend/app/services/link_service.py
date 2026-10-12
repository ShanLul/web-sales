"""临时链接业务逻辑：生成、状态派生、次数原子扣减、启停与作废。

状态策略：数据库只持久化 active / disabled / voided；
expired / exhausted / unused / in_use 均在读取时实时推导，无需定时任务。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import generate_link_token
from app.models.enums import (
    LINK_STATUS_LABELS,
    LinkDerivedStatus,
    LinkStatus,
)
from app.models.permission import PermissionTemplate
from app.models.temp_link import TempLink
from app.schemas.temp_link import TempLinkCreate, TempLinkOut
from app.utils.exceptions import BizError, ErrorCode, NotFoundError

_TOKEN_MAX_RETRY = 5


def derive_status(link: TempLink, now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    if link.status == LinkStatus.VOIDED.value:
        return LinkDerivedStatus.VOIDED.value
    if link.status == LinkStatus.DISABLED.value:
        return LinkDerivedStatus.DISABLED.value
    if link.expire_at is not None and link.expire_at <= now:
        return LinkDerivedStatus.EXPIRED.value
    if link.max_uses is not None and link.used_count >= link.max_uses:
        return LinkDerivedStatus.EXHAUSTED.value
    if link.is_single_use and link.used_count > 0:
        return LinkDerivedStatus.EXHAUSTED.value
    if link.used_count > 0:
        return LinkDerivedStatus.IN_USE.value
    return LinkDerivedStatus.UNUSED.value


def remaining_uses(link: TempLink) -> Optional[int]:
    if link.max_uses is None:
        return None
    if link.is_single_use:
        return max(1 - link.used_count, 0)
    return max(link.max_uses - link.used_count, 0)


def serialize(link: TempLink, now: Optional[datetime] = None) -> TempLinkOut:
    derived = derive_status(link, now)
    return TempLinkOut(
        id=link.id,
        token=link.token,
        url=settings.build_portal_url(link.token),
        template_id=link.template_id,
        template_name=link.template.name if link.template else None,
        remark=link.remark,
        expire_at=link.expire_at,
        max_uses=link.max_uses,
        used_count=link.used_count,
        remaining_uses=remaining_uses(link),
        is_single_use=link.is_single_use,
        status=link.status,
        derived_status=derived,
        status_label=LINK_STATUS_LABELS.get(derived, derived),
        created_at=link.created_at,
        last_accessed_at=link.last_accessed_at,
    )


def get_link(db: Session, link_id: int) -> TempLink:
    link = db.get(TempLink, link_id)
    if link is None:
        raise NotFoundError("临时链接不存在")
    return link


def get_link_by_token(db: Session, token: str) -> Optional[TempLink]:
    return db.scalar(
        select(TempLink)
        .options(joinedload(TempLink.template))
        .where(TempLink.token == token)
    )


def get_valid_link(db: Session, token: str, now: Optional[datetime] = None) -> TempLink:
    """校验链接可用性；失败时抛出带明确原因码的业务异常。"""
    now = now or datetime.now()
    link = get_link_by_token(db, token)
    if link is None:
        raise BizError("链接不存在或已失效", ErrorCode.LINK_NOT_FOUND)

    derived = derive_status(link, now)
    if derived == LinkDerivedStatus.EXPIRED.value:
        raise BizError("链接已过期", ErrorCode.LINK_EXPIRED)
    if derived == LinkDerivedStatus.EXHAUSTED.value:
        raise BizError("链接可用次数已用完", ErrorCode.LINK_EXHAUSTED)
    if derived == LinkDerivedStatus.DISABLED.value:
        raise BizError("链接已被停用", ErrorCode.LINK_DISABLED)
    if derived == LinkDerivedStatus.VOIDED.value:
        raise BizError("链接已被作废", ErrorCode.LINK_VOIDED)

    if link.template is not None and not link.template.is_active:
        raise BizError("链接关联的权限模板已停用", ErrorCode.LINK_DISABLED)
    return link


def create_link(db: Session, payload: TempLinkCreate) -> TempLink:
    template = db.get(PermissionTemplate, payload.template_id)
    if template is None:
        raise NotFoundError("权限模板不存在")
    if not template.is_active:
        raise BizError("该权限模板已停用，无法生成链接")

    link: Optional[TempLink] = None
    for _ in range(_TOKEN_MAX_RETRY):
        candidate = TempLink(
            token=generate_link_token(),
            template_id=template.id,
            remark=payload.remark or None,
            expire_at=payload.expire_at,
            max_uses=payload.max_uses,
            used_count=0,
            is_single_use=payload.is_single_use,
            status=LinkStatus.ACTIVE.value,
            created_at=datetime.now(),
        )
        db.add(candidate)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        link = candidate
        break

    if link is None:
        raise BizError("链接生成失败，请重试", ErrorCode.INTERNAL, http_status=500)

    db.refresh(link)
    link.template = template
    return link


def consume_use(db: Session, link_id: int, now: Optional[datetime] = None) -> bool:
    """条件行级更新，保证并发下不会超发次数；返回是否扣减成功（不提交事务）。"""
    now = now or datetime.now()
    stmt = (
        update(TempLink)
        .where(
            TempLink.id == link_id,
            TempLink.status == LinkStatus.ACTIVE.value,
            or_(TempLink.expire_at.is_(None), TempLink.expire_at > now),
            or_(TempLink.max_uses.is_(None), TempLink.used_count < TempLink.max_uses),
            or_(TempLink.is_single_use.is_(False), TempLink.used_count == 0),
        )
        .values(used_count=TempLink.used_count + 1, last_accessed_at=now)
        .execution_options(synchronize_session=False)
    )
    result = db.execute(stmt)
    return result.rowcount == 1


def mark_accessed(db: Session, link: TempLink, now: Optional[datetime] = None) -> None:
    link.last_accessed_at = now or datetime.now()
    db.commit()


def set_status(db: Session, link_id: int, new_status: str) -> TempLink:
    link = get_link(db, link_id)
    if link.status == LinkStatus.VOIDED.value:
        raise BizError("链接已作废，无法再次变更状态")
    if new_status not in (LinkStatus.ACTIVE.value, LinkStatus.DISABLED.value):
        raise BizError("不支持的链接状态")
    link.status = new_status
    db.commit()
    db.refresh(link)
    return link


def void_link(db: Session, link_id: int) -> TempLink:
    link = get_link(db, link_id)
    if link.status == LinkStatus.VOIDED.value:
        raise BizError("链接已作废，无需重复操作")
    link.status = LinkStatus.VOIDED.value
    db.commit()
    db.refresh(link)
    return link
