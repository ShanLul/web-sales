"""product variant

Revision ID: 0002_product_variant
Revises: 0001_initial
Create Date: 2026-10-12

说明：新增商品规格表，并为订单明细补充规格快照字段。
规格为空即代表商品只有单一价格，因此历史商品与订单无需数据回填。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_product_variant"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "product_variant",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=True),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default=sa.text("'on_sale'")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=NOW),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_variant_product_id", "product_variant", ["product_id"])
    op.create_index("ix_product_variant_sku", "product_variant", ["sku"], unique=True)

    # SQLite 不支持 ALTER TABLE 增加外键约束，batch 模式会自动重建表
    with op.batch_alter_table("sales_order_item") as batch_op:
        batch_op.add_column(sa.Column("variant_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("variant_name", sa.String(length=50), nullable=True))
        batch_op.create_foreign_key(
            "fk_sales_order_item_variant_id",
            "product_variant",
            ["variant_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("sales_order_item") as batch_op:
        batch_op.drop_constraint("fk_sales_order_item_variant_id", type_="foreignkey")
        batch_op.drop_column("variant_name")
        batch_op.drop_column("variant_id")

    op.drop_index("ix_product_variant_sku", table_name="product_variant")
    op.drop_index("ix_product_variant_product_id", table_name="product_variant")
    op.drop_table("product_variant")
