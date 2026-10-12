"""统一导出全部 ORM 模型，供 Alembic 自动生成迁移使用。"""

from app.models.admin import Admin
from app.models.order import Order, OrderItem
from app.models.permission import PermissionTemplate, template_product
from app.models.product import Category, Product, ProductVariant
from app.models.temp_link import TempLink

__all__ = [
    "Admin",
    "Category",
    "Product",
    "ProductVariant",
    "PermissionTemplate",
    "template_product",
    "TempLink",
    "Order",
    "OrderItem",
]
