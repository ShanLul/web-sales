"""权限模板：以「可见商品集合」为单位，可被临时链接复用。"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product

# 模板与商品多对多关联表
template_product = Table(
    "template_product",
    Base.metadata,
    Column(
        "template_id",
        ForeignKey("permission_template.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("product_id", ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
)


class PermissionTemplate(Base, TimestampMixin):
    __tablename__ = "permission_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(
        secondary=template_product,
        order_by="Product.id",
    )
