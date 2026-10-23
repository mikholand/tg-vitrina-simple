from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin

MAX_BANNERS = 3


class Banner(Base, TimestampMixin):
    """A home-page carousel slide. At most `MAX_BANNERS` rows are allowed —
    enforced in `BannerRepository.create`, not at the DB level, matching
    this codebase's convention of keeping such business rules in the
    repository/service layer (see e.g. category depth checks)."""

    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 16:9 crop, shown on narrow/mobile screens.
    image_path_mobile: Mapped[str] = mapped_column(String(300), nullable=False)
    # 4:1 crop, shown on wide/desktop screens. Nullable so banners created
    # before this split still load — the frontend falls back to the mobile
    # image on desktop too until the seller re-uploads one.
    image_path_desktop: Mapped[str | None] = mapped_column(String(300), nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
