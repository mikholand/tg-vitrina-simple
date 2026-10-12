"""Add banners: home-page carousel slides.

A small admin-managed table (at most 3 rows, enforced in the repository,
not here) backing the home page carousel — each row is an image plus an
optional outbound link.

Revision ID: 0003_banners
Revises: 0002_store_profile
Create Date: 2026-10-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_banners"
down_revision: str | None = "0002_store_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "banners",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("image_path", sa.String(300), nullable=False),
        sa.Column("link_url", sa.String(500)),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("banners")
