"""订单与订单明细。表名避开 MySQL 保留字 order。"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import OrderStatus


class Order(Base, TimestampMixin):
    __tablename__ = "sales_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    link_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("temp_link.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # 来源链接备注快照，链接被删也不影响订单可读性
    link_remark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    customer_name: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_address: Mapped[str] = mapped_column(String(255), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(
        String(20), default=OrderStatus.PENDING.value, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )


class OrderItem(Base):
    __tablename__ = "sales_order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("sales_order.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), nullable=True
    )
    variant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("product_variant.id", ondelete="SET NULL"), nullable=True
    )
    # 下单时快照，避免商品改价/改名/规格变更影响历史订单
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variant_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
