"""Add users.tg_photo_url — real Telegram avatar, refreshed on every login.

Telegram only reliably populates `photo_url` for Mini Apps launched from the
attachment menu, so this stays nullable and the frontend keeps its
letter-avatar fallback for everyone else.

Revision ID: 0009_user_photo_url
Revises: 0008_invites
Create Date: 2026-10-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_user_photo_url"
down_revision: str | None = "0008_invites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("tg_photo_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "tg_photo_url")
