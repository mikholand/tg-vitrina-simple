from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.entities.raw_post import RawPostStatus
from app.shared.media import media_url


class RawPostSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    message_id: int
    media_group_id: int | None
    raw_text: str | None
    photo_paths: list[str]
    posted_at: datetime
    status: RawPostStatus
    product_id: int | None
    created_at: datetime

    # See ProductSchema._to_media_urls — same bare-relative-path issue.
    @field_validator("photo_paths", mode="after")
    @classmethod
    def _to_media_urls(cls, value: list[str]) -> list[str]:
        return [media_url(path) for path in value]
