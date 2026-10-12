"""权限模板解析：模板 -> 可见商品集合，以及下单时的服务端授权校验。

设计约定：模板是链接可见范围的唯一来源，落库只写具体商品集合，
「按分类批量勾选」仅作为前端录入交互，不参与服务端解析。
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import ProductStatus
from app.models.permission import PermissionTemplate, template_product
from app.models.product import Product
from app.utils.exceptions import NotFoundError


def get_template(db: Session, template_id: int) -> PermissionTemplate:
    template = db.get(PermissionTemplate, template_id)
    if template is None:
        raise NotFoundError("权限模板不存在")
    return template


def template_product_ids(db: Session, template_id: int) -> list[int]:
    rows = db.execute(
        select(template_product.c.product_id)
        .where(template_product.c.template_id == template_id)
        .order_by(template_product.c.product_id)
    ).scalars()
    return list(rows)


def visible_products(
    db: Session,
    template_id: int,
    only_on_sale: bool = False,
    keyword: Optional[str] = None,
) -> list[Product]:
    """按模板解析可见商品。"""
    stmt = (
        select(Product)
        .join(template_product, template_product.c.product_id == Product.id)
        .where(template_product.c.template_id == template_id)
        # 规格用 selectinload 单独取，避免与 category 的 joinedload 叠加产生行膨胀
        .options(joinedload(Product.category), selectinload(Product.variants))
        .order_by(Product.category_id.is_(None), Product.category_id, Product.id)
    )
    if only_on_sale:
        stmt = stmt.where(Product.status == ProductStatus.ON_SALE.value)
    if keyword:
        stmt = stmt.where(Product.name.like(f"%{keyword.strip()}%"))
    return list(db.execute(stmt).scalars().unique())


def fetch_authorized_products(
    db: Session, template_id: int, product_ids: list[int]
) -> list[Product]:
    """取出指定商品中确实属于该模板授权范围的记录，用于服务端越权校验。"""
    if not product_ids:
        return []
    stmt = (
        select(Product)
        .join(template_product, template_product.c.product_id == Product.id)
        .where(
            template_product.c.template_id == template_id,
            Product.id.in_(product_ids),
        )
        .options(joinedload(Product.category), selectinload(Product.variants))
    )
    return list(db.execute(stmt).scalars().unique())


def replace_template_products(db: Session, template: PermissionTemplate, product_ids: list[int]) -> None:
    """整体替换模板可见商品集合（幂等，未变化的商品不会被误删）。"""
    wanted = set(product_ids)
    if wanted:
        valid_ids = set(
            db.execute(select(Product.id).where(Product.id.in_(wanted))).scalars()
        )
        missing = wanted - valid_ids
        if missing:
            raise NotFoundError(f"以下商品不存在：{sorted(missing)}")
    else:
        valid_ids = set()

    current = set(template_product_ids(db, template.id))
    to_remove = current - valid_ids
    to_add = valid_ids - current

    if to_remove:
        db.execute(
            template_product.delete().where(
                template_product.c.template_id == template.id,
                template_product.c.product_id.in_(to_remove),
            )
        )
    for product_id in sorted(to_add):
        db.execute(
            template_product.insert().values(template_id=template.id, product_id=product_id)
        )
    db.flush()
