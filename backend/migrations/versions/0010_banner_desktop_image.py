"""Split banners.image_path into separate mobile/desktop crops.

The carousel used one image at a fixed 16:9 crop everywhere, which looked
cropped/stretched on wide desktop screens. Sellers now upload a second,
wide 4:1 image for desktop alongside the original 16:9 one. The old
`image_path` column is renamed to `image_path_mobile`; the new
`image_path_desktop` stays nullable so banners uploaded before this split
keep working — the frontend falls back to the mobile image on desktop too
until the seller re-uploads with a dedicated 4:1 crop.

Revision ID: 0010_banner_desktop_image
Revises: 0009_user_photo_url
Create Date: 2026-10-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_banner_desktop_image"
down_revision: str | None = "0009_user_photo_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("banners", "image_path", new_column_name="image_path_mobile")
    op.add_column("banners", sa.Column("image_path_desktop", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("banners", "image_path_desktop")
    op.alter_column("banners", "image_path_mobile", new_column_name="image_path")
