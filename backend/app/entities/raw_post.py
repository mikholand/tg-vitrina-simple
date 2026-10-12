import enum
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class RawPostStatus(enum.StrEnum):
    NEW = "new"
    EXTRACTED = "extracted"
    FAILED = "failed"


class RawPost(Base, TimestampMixin):
    """One Telegram post (or one media group) captured from the store's channel.

    A media group (album) is one post and produces exactly one RawPost — all
    photos in the group are merged into `photo_paths`.
    """

    __tablename__ = "raw_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    media_group_id: Mapped[int | None] = mapped_column(BigInteger)
    raw_text: Mapped[str | None] = mapped_column(Text)
    photo_paths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[RawPostStatus] = mapped_column(
        Enum(RawPostStatus, native_enum=False, length=20),
        default=RawPostStatus.NEW,
        nullable=False,
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="SET NULL")
    )

    # Partial unique constraints (one RawPost per media group, one per lone
    # message) are Postgres-specific and created directly in the migration —
    # dedup is additionally enforced at the repository level before insert.
    __table_args__ = (Index("ix_raw_posts_status", "status"),)
