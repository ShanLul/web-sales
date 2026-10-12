"""订单查看与状态流转。"""

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentAdmin, DbSession
from app.models.order import Order
from app.schemas.common import PageResult, ok
from app.schemas.order import OrderStatusUpdate
from app.services import order_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["主系统-订单"])


class OrderFilters(BaseModel):
    keyword: Optional[str] = None
    link_id: Optional[int] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


OrderFilterDep = Annotated[OrderFilters, Depends()]


def build_stmt(filters: OrderFilters):
    return order_service.build_query(
        keyword=filters.keyword,
        link_id=filters.link_id,
        status=filters.status,
        start_time=filters.start_time,
        end_time=filters.end_time,
    )


@router.get("")
def list_orders(
    db: DbSession,
    _admin: CurrentAdmin,
    filters: OrderFilterDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    stmt = build_stmt(filters)
    total = order_service.count_orders(db, stmt)
    rows = (
        db.execute(
            stmt.options(selectinload(Order.items))
            .order_by(Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .unique()
        .all()
    )
    return ok(
        PageResult(
            items=[order_service.to_out(item) for item in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{order_id}")
def get_order(order_id: int, db: DbSession, _admin: CurrentAdmin):
    return ok(order_service.to_out(order_service.get_order(db, order_id)))


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int, payload: OrderStatusUpdate, db: DbSession, admin: CurrentAdmin
):
    order = order_service.change_status(db, order_id, payload.status)
    logger.info(
        "订单状态变更 order_no=%s status=%s admin=%s", order.order_no, order.status, admin.username
    )
    return ok(order_service.to_out(order))
