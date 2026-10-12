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
    image_path: Mapped[str] = mapped_column(String(300), nullable=False)
    link_url: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
