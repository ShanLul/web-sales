"""商品与分类维护。路由层只做参数校验与编排，规则下沉到服务层与模型约束。"""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.core.deps import CurrentAdmin, DbSession
from app.models.enums import ProductStatus
from app.models.product import Category, Product, ProductVariant
from app.schemas.common import PageResult, ok
from app.schemas.product import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ProductCreate,
    ProductOut,
    ProductStatusUpdate,
    ProductUpdate,
    VariantIn,
    VariantOut,
)
from app.utils.exceptions import BizError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)

_CENT = Decimal("0.01")

router = APIRouter(prefix="/products", tags=["主系统-商品"])
category_router = APIRouter(prefix="/categories", tags=["主系统-分类"])


def _to_out(product: Product) -> ProductOut:
    variants = [VariantOut.model_validate(item) for item in product.variants]
    return ProductOut(
        id=product.id,
        name=product.name,
        sku=product.sku,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        price=float(product.price),
        unit=product.unit,
        image_url=product.image_url,
        description=product.description,
        status=product.status,
        variants=variants,
        variant_count=len(variants),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def _ensure_variant_sku_unique(
    db: DbSession, variants: list[VariantIn], product_id: Optional[int]
) -> None:
    """规格 SKU 全局唯一：列表内部重复已在 schema 层拦掉，这里只查跨商品冲突。"""
    skus = [item.sku for item in variants if item.sku]
    if not skus:
        return
    stmt = select(ProductVariant.sku).where(ProductVariant.sku.in_(skus))
    if product_id is not None:
        stmt = stmt.where(ProductVariant.product_id != product_id)
    conflict = db.scalar(stmt)
    if conflict:
        raise ConflictError(f"规格 SKU「{conflict}」已被其他商品占用")


def _replace_variants(
    db: DbSession, product: Product, variants: list[VariantIn], product_id: Optional[int]
) -> None:
    """整体替换规格集合，列表顺序即展示顺序。"""
    _ensure_variant_sku_unique(db, variants, product_id)
    # delete-orphan 级联会清掉被移除的规格，历史订单明细靠 variant_name 快照保读
    product.variants.clear()
    db.flush()
    for index, item in enumerate(variants):
        product.variants.append(
            ProductVariant(
                name=item.name,
                sku=item.sku,
                price=item.price,
                image_url=item.image_url,
                status=item.status,
                sort_order=index,
            )
        )


def _sync_price_from_variants(product: Product) -> None:
    """多规格商品以最低规格价作为对外起价，保证列表展示与价格筛选口径一致。"""
    candidates = [
        item for item in product.variants if item.status == ProductStatus.ON_SALE.value
    ] or list(product.variants)
    if candidates:
        product.price = min(Decimal(item.price) for item in candidates).quantize(_CENT)


def _get_product(db: DbSession, product_id: int) -> Product:
    product = db.get(
        Product, product_id, options=[joinedload(Product.category), selectinload(Product.variants)]
    )
    if product is None:
        raise NotFoundError("商品不存在")
    return product


def _ensure_sku_unique(db: DbSession, sku: Optional[str], exclude_id: Optional[int] = None) -> None:
    if not sku:
        return
    stmt = select(Product.id).where(Product.sku == sku)
    if exclude_id is not None:
        stmt = stmt.where(Product.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ConflictError(f"SKU「{sku}」已被其他商品占用")


def _ensure_category_exists(db: DbSession, category_id: Optional[int]) -> None:
    if category_id is None:
        return
    if db.get(Category, category_id) is None:
        raise NotFoundError("所属分类不存在")


@router.get("")
def list_products(
    db: DbSession,
    _admin: CurrentAdmin,
    keyword: Optional[str] = Query(None, max_length=100),
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    conditions = []
    if keyword and keyword.strip():
        conditions.append(Product.name.like(f"%{keyword.strip()}%"))
    if category_id:
        conditions.append(Product.category_id == category_id)
    if status:
        conditions.append(Product.status == status)

    total = db.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0
    rows = (
        db.execute(
            select(Product)
            .where(*conditions)
            .options(joinedload(Product.category), selectinload(Product.variants))
            .order_by(Product.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .unique()
        .all()
    )
    return ok(
        PageResult[ProductOut](
            items=[_to_out(item) for item in rows], total=total, page=page, page_size=page_size
        )
    )


@router.get("/{product_id}")
def get_product(product_id: int, db: DbSession, _admin: CurrentAdmin):
    return ok(_to_out(_get_product(db, product_id)))


@router.post("")
def create_product(payload: ProductCreate, db: DbSession, _admin: CurrentAdmin):
    _ensure_sku_unique(db, payload.sku)
    _ensure_category_exists(db, payload.category_id)
    product = Product(**payload.model_dump(exclude={"variants"}))
    db.add(product)
    variants = payload.variants or []
    if variants:
        _replace_variants(db, product, variants, product_id=None)
        _sync_price_from_variants(product)
    db.commit()
    db.refresh(product)
    logger.info("新增商品 id=%s name=%s 规格数=%s", product.id, product.name, len(variants))
    return ok(_to_out(product))


@router.put("/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, db: DbSession, _admin: CurrentAdmin):
    product = _get_product(db, product_id)
    data = payload.model_dump(exclude_unset=True)
    # variants 缺省或显式传 null 均表示不改动规格，传 [] 表示清空规格
    # 这里取原始 VariantIn 对象而非 model_dump 后的 dict，_replace_variants 依赖其属性
    data.pop("variants", None)
    variants = payload.variants if "variants" in payload.model_fields_set else None
    if "sku" in data:
        _ensure_sku_unique(db, data["sku"], exclude_id=product_id)
    if "category_id" in data:
        _ensure_category_exists(db, data["category_id"])
    for field, value in data.items():
        setattr(product, field, value)
    if variants is not None:
        _replace_variants(db, product, variants, product_id=product_id)
        if variants:
            # 有规格时价格由规格决定，忽略本次提交的单价
            _sync_price_from_variants(product)
    db.commit()
    db.refresh(product)
    return ok(_to_out(product))


@router.patch("/{product_id}/status")
def update_product_status(
    product_id: int, payload: ProductStatusUpdate, db: DbSession, _admin: CurrentAdmin
):
    product = _get_product(db, product_id)
    product.status = payload.status
    db.commit()
    db.refresh(product)
    return ok(_to_out(product))


@router.delete("/{product_id}")
def delete_product(product_id: int, db: DbSession, _admin: CurrentAdmin):
    product = _get_product(db, product_id)
    name = product.name
    db.delete(product)
    db.commit()
    logger.info("删除商品 id=%s name=%s", product_id, name)
    return ok({"id": product_id})


# ---------------- 分类 ----------------


@category_router.get("")
def list_categories(db: DbSession, _admin: CurrentAdmin):
    counts = dict(
        db.execute(
            select(Product.category_id, func.count(Product.id)).group_by(Product.category_id)
        ).all()
    )
    categories = db.execute(select(Category).order_by(Category.sort_order, Category.id)).scalars().all()
    return ok(
        [
            CategoryOut(
                id=item.id,
                name=item.name,
                sort_order=item.sort_order,
                product_count=counts.get(item.id, 0),
                created_at=item.created_at,
            )
            for item in categories
        ]
    )


@category_router.post("")
def create_category(payload: CategoryCreate, db: DbSession, _admin: CurrentAdmin):
    if db.scalar(select(Category.id).where(Category.name == payload.name)) is not None:
        raise ConflictError(f"分类「{payload.name}」已存在")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return ok(
        CategoryOut(
            id=category.id, name=category.name, sort_order=category.sort_order, created_at=category.created_at
        )
    )


@category_router.put("/{category_id}")
def update_category(category_id: int, payload: CategoryUpdate, db: DbSession, _admin: CurrentAdmin):
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("分类不存在")
    data = payload.model_dump(exclude_unset=True)
    new_name = data.get("name")
    if new_name and new_name != category.name:
        if db.scalar(select(Category.id).where(Category.name == new_name)) is not None:
            raise ConflictError(f"分类「{new_name}」已存在")
    for field, value in data.items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    count = db.scalar(
        select(func.count(Product.id)).where(Product.category_id == category_id)
    ) or 0
    return ok(
        CategoryOut(
            id=category.id,
            name=category.name,
            sort_order=category.sort_order,
            product_count=count,
            created_at=category.created_at,
        )
    )


@category_router.delete("/{category_id}")
def delete_category(category_id: int, db: DbSession, _admin: CurrentAdmin):
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("分类不存在")
    count = db.scalar(select(func.count(Product.id)).where(Product.category_id == category_id)) or 0
    if count:
        raise BizError(f"该分类下还有 {count} 个商品，请先调整商品分类")
    db.delete(category)
    db.commit()
    return ok({"id": category_id})
