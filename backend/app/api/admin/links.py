"""临时链接管理：生成、列表、启用/禁用、作废。

列表支持按派生状态过滤：SQL 条件与 link_service.derive_status 的判定顺序严格保持一致，
避免「列表显示的状态」与「过滤出的数据」不一致。
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.orm import joinedload

from app.core.deps import CurrentAdmin, DbSession
from app.models.enums import LinkDerivedStatus, LinkStatus
from app.models.permission import PermissionTemplate
from app.models.temp_link import TempLink
from app.schemas.common import PageResult, ok
from app.schemas.temp_link import TempLinkCreate, TempLinkStatusUpdate
from app.services import link_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/temp-links", tags=["主系统-临时链接"])


def _split_conditions(now: datetime):
    """返回 (已过期, 次数耗尽, 仍可用) 三组 SQL 条件。"""
    active = TempLink.status == LinkStatus.ACTIVE.value
    expired = and_(active, TempLink.expire_at.is_not(None), TempLink.expire_at <= now)
    exhausted = and_(
        active,
        not_(expired),
        or_(
            and_(TempLink.max_uses.is_not(None), TempLink.used_count >= TempLink.max_uses),
            and_(TempLink.is_single_use.is_(True), TempLink.used_count > 0),
        ),
    )
    usable = and_(active, not_(expired), not_(exhausted))
    return expired, exhausted, usable


def _derived_condition(derived_status: str, now: datetime):
    expired, exhausted, usable = _split_conditions(now)
    if derived_status == LinkDerivedStatus.VOIDED.value:
        return TempLink.status == LinkStatus.VOIDED.value
    if derived_status == LinkDerivedStatus.DISABLED.value:
        return TempLink.status == LinkStatus.DISABLED.value
    if derived_status == LinkDerivedStatus.EXPIRED.value:
        return expired
    if derived_status == LinkDerivedStatus.EXHAUSTED.value:
        return exhausted
    if derived_status == LinkDerivedStatus.IN_USE.value:
        return and_(usable, TempLink.used_count > 0)
    if derived_status == LinkDerivedStatus.UNUSED.value:
        return and_(usable, TempLink.used_count == 0)
    # 未知筛选值：返回恒不成立条件，避免静默退化为返回全部数据
    return TempLink.id.is_(None)


@router.get("")
def list_links(
    db: DbSession,
    _admin: CurrentAdmin,
    keyword: Optional[str] = Query(None, max_length=200),
    derived_status: Optional[str] = Query(None),
    template_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    now = datetime.now()
    conditions = []
    if keyword and keyword.strip():
        text = keyword.strip()
        conditions.append(
            or_(
                TempLink.remark.like(f"%{text}%"),
                TempLink.token.like(f"%{text}%"),
                TempLink.template.has(PermissionTemplate.name.like(f"%{text}%")),
            )
        )
    if template_id:
        conditions.append(TempLink.template_id == template_id)
    if derived_status:
        conditions.append(_derived_condition(derived_status, now))

    total = db.scalar(select(func.count()).select_from(TempLink).where(*conditions)) or 0
    rows = (
        db.execute(
            select(TempLink)
            .where(*conditions)
            .options(joinedload(TempLink.template))
            .order_by(TempLink.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .unique()
        .all()
    )
    return ok(
        PageResult(
            items=[link_service.serialize(item, now) for item in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("")
def create_link(payload: TempLinkCreate, db: DbSession, admin: CurrentAdmin):
    link = link_service.create_link(db, payload)
    logger.info(
        "生成临时链接 id=%s template_id=%s admin=%s expire_at=%s max_uses=%s single_use=%s",
        link.id,
        link.template_id,
        admin.username,
        link.expire_at,
        link.max_uses,
        link.is_single_use,
    )
    return ok(link_service.serialize(link))


@router.get("/{link_id}")
def get_link(link_id: int, db: DbSession, _admin: CurrentAdmin):
    link = link_service.get_link(db, link_id)
    return ok(link_service.serialize(link))


@router.patch("/{link_id}/status")
def update_link_status(
    link_id: int, payload: TempLinkStatusUpdate, db: DbSession, admin: CurrentAdmin
):
    link = link_service.set_status(db, link_id, payload.status)
    logger.info("链接状态变更 id=%s status=%s admin=%s", link.id, link.status, admin.username)
    return ok(link_service.serialize(link))


@router.post("/{link_id}/void")
def void_link(link_id: int, db: DbSession, admin: CurrentAdmin):
    link = link_service.void_link(db, link_id)
    logger.info("链接作废 id=%s admin=%s", link.id, admin.username)
    return ok(link_service.serialize(link))
