from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.entities.order import OrderStatus


class CartItemInputSchema(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CheckoutRequestSchema(BaseModel):
    items: list[CartItemInputSchema]
    comment: str | None = None


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    product_name: str
    price: Decimal
    currency: str
    quantity: int


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None
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
