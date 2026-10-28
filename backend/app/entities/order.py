import enum
from decimal import Decimal

from sqlalchemy import BigInteger, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class OrderStatus(enum.StrEnum):
    """Order lifecycle as the seller moves it along in the cabinet
    (`OrderService.change_status`) and the customer sees it in their
    profile. Added without a migration — the column is a plain string enum
    (`native_enum=False`), so only `length=20` bounds new values.

    Deliberately no enforced transition graph: a seller who taps the wrong
    status must be able to put it back, and a single shop's handful of
    staff doesn't need a workflow engine guarding them from themselves."""

    NEW = "new"
    ACCEPTED = "accepted"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base, TimestampMixin):
    """A customer's cart, snapshotted at checkout time and forwarded to the
    seller's Telegram chat (see `OrderService`/`BotClient.notify_order`).

    Line items live in `OrderItem`, not JSON on this row — same normalized
    shape as `products`/`product_categories` — so the seller order-history
    view (`GET /seller/orders`) can list/paginate orders without parsing a
    blob, and so a line item's price/name are frozen at purchase time even
    if the product is edited or deleted afterwards.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Set when checkout happens inside the Telegram Mini App (`OptionalUser`
    # resolves a real `User`). Null for a guest checkout from the plain
    # website, where `contact_name`/`contact_phone` carry the customer's
    # identity instead — see `OrderService.checkout`. Also nullable + SET
    # NULL for safety if a user row is ever removed in the future — the
    # order itself, and its already-sent notification, must survive that.
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    # Required by `OrderService.checkout` whenever `customer_id` is None (no
    # Telegram identity to fall back on); always optional on the column
    # itself since a Telegram-authenticated checkout never needs them.
    contact_name: Mapped[str | None] = mapped_column(String(200))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.NEW,
        nullable=False,
    )
    # True once `BotClient.notify_order` has actually been sent — surfaced in
    # the seller order list so a seller can tell a checkout that silently
    # failed to reach the chat (e.g. the bot was removed) apart from one
    # where it genuinely never going to send.
    notified: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (Index("ix_orders_customer_id", "customer_id"),)


class OrderItem(Base):
    """A single product line, frozen at checkout: name/price/currency are
    copied from the `Product` row at that moment rather than referenced live,
    so later edits (or deletion) of the product never rewrite history."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    # Kept for a "go to product" link in the seller order view when it still
    # exists; SET NULL (not CASCADE) so deleting a product never deletes the
    # historical order line that references it.
    product_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="SET NULL")
    )
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # First product photo at checkout time (MEDIA_ROOT-relative, like every
    # other stored media path) — a thumbnail for the order history lists.
    # Unlike name/price this points at the product's own file rather than a
    # copy, so `ProductService.delete_product` removing that file leaves a
    # dangling path: both order lists fall back to a placeholder icon when
    # the image fails to load instead of copying a file per order line.
    photo_path: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (Index("ix_order_items_order_id", "order_id"),)
