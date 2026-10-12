"""权限模板维护：模板本身 CRUD + 可见商品集合设置。"""

import logging
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.deps import CurrentAdmin, DbSession
from app.models.permission import PermissionTemplate, template_product
from app.models.temp_link import TempLink
from app.schemas.common import PageResult, ok
from app.schemas.permission import TemplateCreate, TemplateDuplicate, TemplateOut, TemplateUpdate
from app.schemas.product import ProductBrief
from app.services import permission_service
from app.utils.exceptions import BizError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permission-templates", tags=["主系统-权限模板"])


def _to_out(template: PermissionTemplate, product_ids: Optional[list[int]] = None) -> TemplateOut:
    ids = sorted(product_ids or [])
    return TemplateOut(
        id=template.id,
        name=template.name,
        description=template.description,
        is_active=template.is_active,
        product_count=len(ids),
        product_ids=ids,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _get_template(db: DbSession, template_id: int) -> PermissionTemplate:
    return permission_service.get_template(db, template_id)


def _ensure_name_unique(db: DbSession, name: str, exclude_id: Optional[int] = None) -> None:
    stmt = select(PermissionTemplate.id).where(PermissionTemplate.name == name)
    if exclude_id is not None:
        stmt = stmt.where(PermissionTemplate.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ConflictError(f"模板名称「{name}」已存在")


@router.get("")
def list_templates(
    db: DbSession,
    _admin: CurrentAdmin,
    keyword: Optional[str] = Query(None, max_length=80),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    conditions = []
    if keyword and keyword.strip():
        conditions.append(PermissionTemplate.name.like(f"%{keyword.strip()}%"))

    total = db.scalar(select(func.count()).select_from(PermissionTemplate).where(*conditions)) or 0
    templates = (
        db.execute(
            select(PermissionTemplate)
            .where(*conditions)
            .order_by(PermissionTemplate.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    # 列表需带上可见商品集合：前端编辑器直接用它渲染勾选状态，避免逐个模板再查详情
    ids_by_template: dict[int, list[int]] = {}
    rows = db.execute(
        select(template_product.c.template_id, template_product.c.product_id)
        .where(template_product.c.template_id.in_([item.id for item in templates] or [0]))
        .order_by(template_product.c.product_id)
    ).all()
    for template_id, product_id in rows:
        ids_by_template.setdefault(template_id, []).append(product_id)

    items = [_to_out(template, ids_by_template.get(template.id)) for template in templates]
    return ok(PageResult[TemplateOut](items=items, total=total, page=page, page_size=page_size))


@router.get("/options")
def list_template_options(db: DbSession, _admin: CurrentAdmin):
    """生成链接时的模板下拉选项，只返回启用中的模板。"""
    templates = (
        db.execute(
            select(PermissionTemplate)
            .where(PermissionTemplate.is_active.is_(True))
            .order_by(PermissionTemplate.id.desc())
        )
        .scalars()
        .all()
    )
    counts = dict(
        db.execute(
            select(template_product.c.template_id, func.count(template_product.c.product_id)).group_by(
                template_product.c.template_id
            )
        ).all()
    )
    return ok(
        [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "product_count": counts.get(item.id, 0),
            }
            for item in templates
        ]
    )


@router.get("/{template_id}")
def get_template(template_id: int, db: DbSession, _admin: CurrentAdmin):
    template = _get_template(db, template_id)
    ids = permission_service.template_product_ids(db, template_id)
    return ok(_to_out(template, ids))


@router.get("/{template_id}/products")
def get_template_products(template_id: int, db: DbSession, _admin: CurrentAdmin):
    template = _get_template(db, template_id)
    products = permission_service.visible_products(db, template.id)
    return ok(
        [
            ProductBrief(
                id=item.id,
                name=item.name,
                price=float(item.price),
                unit=item.unit,
                image_url=item.image_url,
                description=item.description,
                category_id=item.category_id,
                category_name=item.category.name if item.category else None,
            )
            for item in products
        ]
    )


@router.post("")
def create_template(payload: TemplateCreate, db: DbSession, _admin: CurrentAdmin):
    _ensure_name_unique(db, payload.name)
    template = PermissionTemplate(
        name=payload.name, description=payload.description, is_active=payload.is_active
    )
    db.add(template)
    db.flush()
    permission_service.replace_template_products(db, template, payload.product_ids)
    db.commit()
    db.refresh(template)
    logger.info("新增权限模板 id=%s name=%s", template.id, template.name)
    return ok(_to_out(template, permission_service.template_product_ids(db, template.id)))


@router.put("/{template_id}")
def update_template(template_id: int, payload: TemplateUpdate, db: DbSession, _admin: CurrentAdmin):
    template = _get_template(db, template_id)
    data = payload.model_dump(exclude_unset=True, exclude={"product_ids"})
    if "name" in data and data["name"] != template.name:
        _ensure_name_unique(db, data["name"], exclude_id=template_id)
    for field, value in data.items():
        setattr(template, field, value)
    if payload.product_ids is not None:
        permission_service.replace_template_products(db, template, payload.product_ids)
    db.commit()
    db.refresh(template)
    return ok(_to_out(template, permission_service.template_product_ids(db, template_id)))


@router.post("/{template_id}/duplicate")
def duplicate_template(
    template_id: int, payload: TemplateDuplicate, db: DbSession, _admin: CurrentAdmin
):
    source = _get_template(db, template_id)
    _ensure_name_unique(db, payload.name)
    ids = permission_service.template_product_ids(db, template_id)
    clone = PermissionTemplate(
        name=payload.name,
        description=source.description,
        is_active=True,
    )
    db.add(clone)
    db.flush()
    permission_service.replace_template_products(db, clone, ids)
    db.commit()
    db.refresh(clone)
    return ok(_to_out(clone, permission_service.template_product_ids(db, clone.id)))


@router.delete("/{template_id}")
def delete_template(template_id: int, db: DbSession, _admin: CurrentAdmin):
    template = _get_template(db, template_id)
    used = db.scalar(
        select(func.count(TempLink.id)).where(TempLink.template_id == template_id)
    ) or 0
    if used:
        raise BizError(f"该模板已被 {used} 条临时链接引用，请先停用模板而非删除")
    db.delete(template)
    db.commit()
    return ok({"id": template_id})
