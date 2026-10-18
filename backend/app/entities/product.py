import enum
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class Availability(enum.StrEnum):
    IN_STOCK = "in_stock"
    ON_ORDER = "on_order"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"


class ProductStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    HIDDEN = "hidden"


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sku: Mapped[str | None] = mapped_column(String(100))
    availability: Mapped[Availability] = mapped_column(
        Enum(Availability, native_enum=False, length=20),
        default=Availability.UNKNOWN,
        nullable=False,
    )
    quantity: Mapped[int | None] = mapped_column(Integer)
    photo_paths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    # At most one video per product (unlike photos, there's no gallery of
    # them) — set via its own upload endpoint, same as photos, never through
    # the create/update JSON body.
    video_path: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False, length=20),
        default=ProductStatus.DRAFT,
        nullable=False,
    )
    # Iron rule: once true, the extractor must never overwrite this product again.
    edited_by_seller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_post_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("raw_posts.id", ondelete="SET NULL")
    )
    publish_to_channel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger)
    views_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_products_quantity_non_negative"),
        Index("ix_products_status", "status"),
        Index("ix_products_sku", "sku"),
    )
