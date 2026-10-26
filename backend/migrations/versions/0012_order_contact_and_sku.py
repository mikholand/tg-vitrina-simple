"""Add orders.contact_name/contact_phone (checkout from the plain website,
outside the Telegram Mini App, has no Telegram identity to fall back on) and
order_items.sku (shown alongside the product name in the Telegram
notification).

Revision ID: 0012_order_contact_and_sku
Revises: 0011_orders
Create Date: 2026-10-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_order_contact_and_sku"
down_revision: str | None = "0011_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("contact_name", sa.String(200), nullable=True))
    op.add_column("orders", sa.Column("contact_phone", sa.String(50), nullable=True))
    op.add_column("order_items", sa.Column("sku", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("order_items", "sku")
    op.drop_column("orders", "contact_phone")
    op.drop_column("orders", "contact_name")
