"""订单业务逻辑：匿名下单（授权校验 + 次数原子扣减 + 商品快照）、状态流转、查询。"""

import secrets
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    ORDER_STATUS_FLOW,
    ORDER_STATUS_LABELS,
    OrderStatus,
    ProductStatus,
)
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductVariant
from app.schemas.order import OrderOut, PortalOrderCreate
from app.services import link_service, permission_service
from app.utils.exceptions import BizError, ErrorCode, NotFoundError

_CENT = Decimal("0.01")


def _generate_order_no(now: datetime) -> str:
    return f"SO{now.strftime('%Y%m%d%H%M%S')}{secrets.randbelow(10000):04d}"


def _resolve_variants(
    ordered: dict[tuple[int, Optional[int]], int],
    product_map: dict[int, Product],
) -> dict[tuple[int, Optional[int]], Optional[ProductVariant]]:
    """校验规格归属与在售状态，并返回「明细键 -> 规格」映射。

    规格信息完全由服务端从数据库取，不信任前端提交的名称与价格。
    """
    resolved: dict[tuple[int, Optional[int]], Optional[ProductVariant]] = {}
    for product_id, variant_id in ordered:
        product = product_map[product_id]
        if variant_id is None:
            # 有规格的商品必须显式选定规格，避免绕过规格直接按商品底价下单
            if product.on_sale_variants:
                raise BizError(
                    f"商品「{product.name}」需要选择规格，请刷新页面后重新选择",
                    ErrorCode.VARIANT_CHANGED,
                )
            resolved[(product_id, None)] = None
            continue

        variant = next((item for item in product.variants if item.id == variant_id), None)
        if variant is None:
            raise BizError("商品规格已变更，请刷新页面后重新选择", ErrorCode.VARIANT_CHANGED)
        if variant.status != ProductStatus.ON_SALE.value:
            raise BizError(
                f"规格「{variant.name}」已下架，请重新选择", ErrorCode.VARIANT_CHANGED
            )
        resolved[(product_id, variant_id)] = variant
    return resolved


def create_portal_order(db: Session, payload: PortalOrderCreate) -> Order:
    """子系统匿名下单。授权范围完全由服务端从 token 推导，不信任前端提交的范围。"""
    now = datetime.now()
    link = link_service.get_valid_link(db, payload.token, now)

    if not payload.items:
        raise BizError("请至少选择一个商品", ErrorCode.EMPTY_CART)

    # 同一商品的不同规格是独立明细行，因此以「商品 + 规格」为键
    ordered: dict[tuple[int, Optional[int]], int] = {
        (item.product_id, item.variant_id): item.quantity for item in payload.items
    }
    product_ids = sorted({product_id for product_id, _ in ordered})
    products = permission_service.fetch_authorized_products(db, link.template_id, product_ids)
    product_map = {product.id: product for product in products}

    missing = set(product_ids) - set(product_map)
    if missing:
        raise BizError("存在不在授权范围内的商品，请刷新后重试", ErrorCode.PRODUCT_NOT_AUTHORIZED)

    off_shelf = [
        product_map[product_id].name
        for product_id, _ in ordered
        if product_map[product_id].status != ProductStatus.ON_SALE.value
    ]
    if off_shelf:
        raise BizError(f"商品「{off_shelf[0]}」已下架，请重新选择", ErrorCode.PRODUCT_OFF_SHELF)

    variant_map = _resolve_variants(ordered, product_map)

    # 原子扣减可用次数（与订单写入在同一事务内，失败则一并回滚）
    if not link_service.consume_use(db, link.id, now):
        db.rollback()
        raise BizError("链接可用次数已用完或已失效", ErrorCode.LINK_EXHAUSTED)

    total = Decimal("0.00")
    details: list[OrderItem] = []
    for key, quantity in ordered.items():
        product_id, _ = key
        product = product_map[product_id]
        variant = variant_map[key]
        price = Decimal(variant.price if variant else product.price).quantize(_CENT)
        subtotal = (price * quantity).quantize(_CENT)
        total += subtotal
        details.append(
            OrderItem(
                product_id=product.id,
                variant_id=variant.id if variant else None,
                product_name=product.name,
                variant_name=variant.name if variant else None,
                price=price,
                quantity=quantity,
                subtotal=subtotal,
            )
        )

    order = Order(
        order_no=_generate_order_no(now),
        link_id=link.id,
        link_remark=link.remark,
        customer_name=payload.customer_name.strip(),
        customer_phone=payload.customer_phone,
        customer_address=payload.customer_address.strip(),
        remark=(payload.remark or "").strip() or None,
        total_amount=total.quantize(_CENT),
        status=OrderStatus.PENDING.value,
        created_at=now,
        items=details,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int, with_items: bool = True) -> Order:
    stmt = select(Order).where(Order.id == order_id)
    if with_items:
        stmt = stmt.options(selectinload(Order.items))
    order = db.scalar(stmt)
    if order is None:
        raise NotFoundError("订单不存在")
    return order


def change_status(db: Session, order_id: int, new_status: str) -> Order:
    order = get_order(db, order_id)
    allowed = ORDER_STATUS_FLOW.get(order.status, [])
    if new_status not in allowed:
        current_label = ORDER_STATUS_LABELS.get(order.status, order.status)
        target_label = ORDER_STATUS_LABELS.get(new_status, new_status)
        raise BizError(f"订单当前为「{current_label}」，不能变更为「{target_label}」")
    order.status = new_status
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def build_query(
    keyword: Optional[str] = None,
    link_id: Optional[int] = None,
    status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    link_keyword: Optional[str] = None,
) -> Select:
    stmt = select(Order)
    if keyword:
        text = keyword.strip()
        stmt = stmt.where(
            Order.order_no.like(f"%{text}%")
            | Order.customer_name.like(f"%{text}%")
            | Order.customer_phone.like(f"%{text}%")
        )
    if link_id:
        stmt = stmt.where(Order.link_id == link_id)
    if link_keyword:
        stmt = stmt.where(Order.link_remark.like(f"%{link_keyword.strip()}%"))
    if status:
        stmt = stmt.where(Order.status == status)
    if start_time:
        stmt = stmt.where(Order.created_at >= start_time)
    if end_time:
        stmt = stmt.where(Order.created_at <= end_time)
    return stmt.order_by(Order.id.desc())


def count_orders(db: Session, stmt: Select) -> int:
    return db.scalar(select(func.count()).select_from(stmt.subquery())) or 0


def to_out(order: Order) -> OrderOut:
    data = OrderOut.model_validate(order)
    data.status_label = ORDER_STATUS_LABELS.get(order.status, order.status)
    data.item_count = sum(item.quantity for item in order.items) if order.items else 0
    return data
