import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base


class StoreView(Base):
    """Unique-visitor-per-day counter for the storefront as a whole.

    Deduplicated: at most one row per (user_id or visitor_key) per calendar day.
    """

    __tablename__ = "store_views"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    visitor_key: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    view_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NULL) <> (visitor_key IS NULL)", name="ck_store_views_one_identity"
        ),
        UniqueConstraint(
            "user_id",
            "visitor_key",
            "view_date",
            name="uq_store_views_dedup",
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_store_views_view_date", "view_date"),
    )


class ProductView(Base):
    """Every single product-card open — intentionally NOT deduplicated.

    `products.views_total` is incremented in the same transaction as the
    insert here; the two must always stay in sync.
    """

    __tablename__ = "product_views"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    visitor_key: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NULL) <> (visitor_key IS NULL)", name="ck_product_views_one_identity"
        ),
        Index("ix_product_views_product_id", "product_id"),
    )
