"""Add store_profile: the seller-editable store identity.

Previously name/description/logo/contact_tg lived only in `STORE_*` env
vars, read-only from the admin UI. This introduces a DB-backed singleton
row (same id=1 convention as `sync_state`) so the seller can actually edit
them through the settings page, matching the admin-editable settings that
exist in the original `tg-vitrina` project. The row is seeded lazily by
`StoreProfileRepository.get()` on first read (from the current env values),
not by this migration, so it works the same on a fresh install and on an
existing deployment.

Revision ID: 0002_store_profile
Revises: 0001_initial_schema
Create Date: 2026-10-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_store_profile"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "store_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("logo", sa.String(300)),
        sa.Column("contact_tg", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("store_profile")
