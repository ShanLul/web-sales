"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-12

说明：所有类型与默认值均按 MySQL 8 / SQLite 双兼容编写，
显式命名索引，便于后续增量迁移与问题排查。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "admin",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False, server_default=sa.text("''")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_username", "admin", ["username"], unique=True)

    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_category_name", "category", ["name"], unique=True)

    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default=sa.text("'件'")),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'on_sale'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_name", "product", ["name"])
    op.create_index("ix_product_sku", "product", ["sku"], unique=True)
    op.create_index("ix_product_category_id", "product", ["category_id"])
    op.create_index("ix_product_status", "product", ["status"])

    op.create_table(
        "permission_template",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_permission_template_name", "permission_template", ["name"], unique=True)

    op.create_table(
        "template_product",
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["permission_template.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("template_id", "product_id"),
    )
    op.create_index("ix_template_product_product_id", "template_product", ["product_id"])

    op.create_table(
        "temp_link",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("remark", sa.String(length=200), nullable=True),
        sa.Column("expire_at", sa.DateTime(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_single_use", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["template_id"], ["permission_template.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_temp_link_token", "temp_link", ["token"], unique=True)
    op.create_index("ix_temp_link_template_id", "temp_link", ["template_id"])
    op.create_index("ix_temp_link_status", "temp_link", ["status"])

    op.create_table(
        "sales_order",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=True),
        sa.Column("link_remark", sa.String(length=200), nullable=True),
        sa.Column("customer_name", sa.String(length=50), nullable=False),
        sa.Column("customer_phone", sa.String(length=20), nullable=False),
        sa.Column("customer_address", sa.String(length=255), nullable=False),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column(
            "total_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["link_id"], ["temp_link.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_order_order_no", "sales_order", ["order_no"], unique=True)
    op.create_index("ix_sales_order_link_id", "sales_order", ["link_id"])
    op.create_index("ix_sales_order_status", "sales_order", ["status"])
    op.create_index("ix_sales_order_created_at", "sales_order", ["created_at"])

    op.create_table(
        "sales_order_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["sales_order.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_order_item_order_id", "sales_order_item", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_order_item_order_id", table_name="sales_order_item")
    op.drop_table("sales_order_item")

    op.drop_index("ix_sales_order_created_at", table_name="sales_order")
    op.drop_index("ix_sales_order_status", table_name="sales_order")
    op.drop_index("ix_sales_order_link_id", table_name="sales_order")
    op.drop_index("ix_sales_order_order_no", table_name="sales_order")
    op.drop_table("sales_order")

    op.drop_index("ix_temp_link_status", table_name="temp_link")
    op.drop_index("ix_temp_link_template_id", table_name="temp_link")
    op.drop_index("ix_temp_link_token", table_name="temp_link")
    op.drop_table("temp_link")

    op.drop_index("ix_template_product_product_id", table_name="template_product")
    op.drop_table("template_product")

    op.drop_index("ix_permission_template_name", table_name="permission_template")
    op.drop_table("permission_template")

    op.drop_index("ix_product_status", table_name="product")
    op.drop_index("ix_product_category_id", table_name="product")
    op.drop_index("ix_product_sku", table_name="product")
    op.drop_index("ix_product_name", table_name="product")
    op.drop_table("product")

    op.drop_index("ix_category_name", table_name="category")
    op.drop_table("category")

    op.drop_index("ix_admin_username", table_name="admin")
    op.drop_table("admin")
