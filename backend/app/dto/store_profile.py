from pydantic import BaseModel


class StoreProfileUpdateSchema(BaseModel):
    """All fields optional — PATCH semantics, only sent fields change."""

    name: str | None = None
    description: str | None = None
    contact_tg: str | None = None


class SellerSettingsSchema(BaseModel):
    """Combined view the seller settings page renders: the admin-editable
    store identity (DB-backed) plus the handful of fields that remain
    deployment-level env config (channel id, extractor availability)."""

    store_name: str
    store_description: str
    store_logo: str | None
    store_contact_tg: str | None
    telegram_channel_id: int
    extractor_configured: bool
