from pydantic import BaseModel, ConfigDict, field_validator

from app.shared.media import media_url


class BannerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    link_url: str | None
    sort_order: int

    @field_validator("image_path")
    @classmethod
    def _to_url(cls, v: str) -> str:
        return media_url(v)


class BannerUpdateSchema(BaseModel):
    """PATCH semantics — `link_url` is distinguished from "omitted" via
    `model_fields_set` in the endpoint, so it can be explicitly cleared."""

    link_url: str | None = None
    sort_order: int | None = None
