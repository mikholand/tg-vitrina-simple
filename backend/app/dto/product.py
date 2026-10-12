from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.entities.product import Availability, ProductStatus
from app.shared.media import media_url


class ProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal | None
    currency: str
    description: str | None
    sku: str | None
    availability: Availability
    quantity: int | None
    photo_paths: list[str]

    # `photo_paths` on the entity holds bare storage-relative paths (e.g.
    # "products/5/abc.jpg", written by save_product_photo/the userbot). The
    # frontend renders these straight as <img src>, so they must come out of
    # the API as host-relative URLs (/media/...), not bare relative paths —
    # a bare path resolves against the *current page* URL in the browser,
    # not the site root, and silently 404s depending on the current route.
    @field_validator("photo_paths", mode="after")
    @classmethod
    def _to_media_urls(cls, value: list[str]) -> list[str]:
        return [media_url(path) for path in value]
    status: ProductStatus
    edited_by_seller: bool
    publish_to_channel: bool
    views_total: int
    created_at: datetime
    updated_at: datetime
    category_ids: list[int] = []


class ProductUpdateSchema(BaseModel):
    name: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    sku: str | None = None
    availability: Availability | None = None
    quantity: int | None = None
    category_ids: list[int] | None = None
    publish_to_channel: bool | None = None


class ProductStatusUpdateSchema(BaseModel):
    status: ProductStatus
