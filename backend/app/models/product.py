"""商品分类、商品与商品规格。"""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ProductStatus

if TYPE_CHECKING:
    from app.models.permission import PermissionTemplate


class Category(Base, TimestampMixin):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base, TimestampMixin):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    unit: Mapped[str] = mapped_column(String(20), default="件", nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=ProductStatus.ON_SALE.value, nullable=False, index=True
    )

    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.sort_order, ProductVariant.id",
    )

    @property
    def category_name(self) -> Optional[str]:
        return self.category.name if self.category else None

    @property
    def on_sale_variants(self) -> list["ProductVariant"]:
        return [item for item in self.variants if item.status == ProductStatus.ON_SALE.value]


class ProductVariant(Base, TimestampMixin):
    """商品规格（口味 / 容量 / 型号等）。

    刻意做成单维度互斥列表，不表达「颜色 × 尺码」这类组合维度：
    对「手工录入 + 单品规格数有限」的销售场景，平铺列表比笛卡尔积矩阵更好维护。
    规格为空时商品退化为单一价格，与历史数据完全兼容。
    """

    __tablename__ = "product_variant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ProductStatus.ON_SALE.value, nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="variants")
