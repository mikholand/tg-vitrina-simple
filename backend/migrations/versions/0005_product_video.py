"""Add products.video_path: a single optional video per product.

Lets sellers attach a video to a product (uploaded via its own endpoint,
POST /seller/products/{id}/video, mirroring the existing photo-upload
endpoint) — in addition to the existing photo gallery, not instead of it.
Nullable, no default: existing products simply have no video until one is
uploaded.

Revision ID: 0005_product_video
Revises: 0004_replace_categories
Create Date: 2026-10-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_product_video"
down_revision: str | None = "0004_replace_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("video_path", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "video_path")
