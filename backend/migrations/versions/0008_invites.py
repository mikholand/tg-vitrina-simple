"""Add invites: one-time links for adding moderators to the team.

Replaces the old "paste the person's numeric Telegram ID" flow — the owner
now generates a link, shares it (Telegram share sheet or plain copy), and
whoever opens it is promoted to moderator. `created_by`/`used_by` store raw
Telegram user ids (same convention as `users.id`), no FK since this is a
single-tenant app.

Revision ID: 0008_invites
Revises: 0007_contacts
Create Date: 2026-10-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_invites"
down_revision: str | None = "0007_contacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("used_by", sa.BigInteger(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("invites")
