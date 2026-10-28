from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.entities.order import OrderStatus
from app.shared.media import media_url


class CartItemInputSchema(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CheckoutRequestSchema(BaseModel):
    items: list[CartItemInputSchema]
    comment: str | None = None
    # Required by `OrderService.checkout` for a guest checkout (no Telegram
    # session) — see `app/api/deps.OptionalUser` on the `/orders` route.
    contact_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=50)


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    product_name: str
    sku: str | None
    price: Decimal
    currency: str
    quantity: int
    photo_path: str | None = None

    # Same bare-relative-path → /media/... URL conversion as
    # `ProductSchema._to_media_urls`, for the same reason.
    @field_validator("photo_path", mode="after")
    @classmethod
    def _to_media_url(cls, value: str | None) -> str | None:
        return media_url(value) if value is not None else None


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None
    contact_name: str | None
    contact_phone: str | None
    total: Decimal
    currency: str
    comment: str | None
    status: OrderStatus
    notified: bool
    created_at: datetime
    # Populated by the API layer (`_to_schema` in `app/api/catalog.py` /
    # `app/api/seller/orders.py`) — the ORM object has no `items` attribute
    # of its own (no `relationship()` anywhere in this codebase, see
    # `OrderRepository`), so this is never auto-filled by `from_attributes`.
    items: list[OrderItemSchema] = []


class OrderCustomerSchema(BaseModel):
    """Who placed a Telegram-authenticated order — the seller needs a name
    and a way to write to them, and `customer_id` alone is neither."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tg_username: str | None
    tg_first_name: str | None
    tg_last_name: str | None


class SellerOrderSchema(OrderSchema):
    """Seller-side view of an order: the customer's own `OrderSchema` plus
    their Telegram identity. Kept off `OrderSchema` itself so the
    customer-facing endpoints don't grow a field that only ever describes
    the caller back to themselves. Null for a guest checkout —
    `contact_name`/`contact_phone` identify those."""

    customer: OrderCustomerSchema | None = None


class OrderStatusUpdateSchema(BaseModel):
    status: OrderStatus
