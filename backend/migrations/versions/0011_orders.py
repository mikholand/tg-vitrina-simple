"""Add orders/order_items (customer cart checkout) and
store_profile.order_notification_chat_id.

A checkout snapshots the cart into `orders` + `order_items` (name/price
frozen at purchase time, independent of later product edits/deletion) and
is forwarded to a Telegram chat. That chat is configured by an admin-only
bot command (`/setorderchat`, run from inside the target chat), which just
sets `store_profile.order_notification_chat_id` — nullable, so existing
deployments keep working with checkout notifications simply disabled until
an admin runs the command once.

Revision ID: 0011_orders
Revises: 0010_banner_desktop_image
Create Date: 2026-10-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_orders"
down_revision: str | None = "0010_banner_desktop_image"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "store_profile", sa.Column("order_notification_chat_id", sa.BigInteger(), nullable=True)
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("comment", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("notified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.BigInteger(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id", sa.BigInteger(), sa.ForeignKey("products.id", ondelete="SET NULL")
        ),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_column("store_profile", "order_notification_chat_id")
