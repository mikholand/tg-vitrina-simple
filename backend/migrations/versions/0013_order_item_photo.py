"""Add order_items.photo_path — a thumbnail for the customer's and the
seller's order history lists, snapshotted at checkout like the line's
name/price. New order statuses (accepted/shipped/completed/cancelled) need
no migration: orders.status is a non-native string enum.

Revision ID: 0013_order_item_photo
Revises: 0012_order_contact_and_sku
Create Date: 2026-10-28
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_order_item_photo"
down_revision: str | None = "0012_order_contact_and_sku"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("order_items", sa.Column("photo_path", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("order_items", "photo_path")
