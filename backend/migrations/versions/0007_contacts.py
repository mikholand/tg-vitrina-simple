"""Add contacts: seller's list of managers buyers can write to.

Replaces the single `store_profile.contact_tg` field with a proper list —
a seller can now register several managers (each with a label, a contact
type, and a value) instead of exactly one Telegram username. The old
`contact_tg` column is left untouched as a legacy fallback: the public
catalog endpoint synthesizes a single contact from it when this table is
empty, so storefronts that never got a manager added keep working.

Single-tenant, like `banners` — no shop scoping, and the "at most 10
contacts" rule is enforced in the repository, not here.

Revision ID: 0007_contacts
Revises: 0006_fix_category_typos
Create Date: 2026-10-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_contacts"
down_revision: str | None = "0006_fix_category_typos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("value", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("contacts")
