from pydantic import BaseModel, ConfigDict, field_validator

from app.shared.media import media_url


class BannerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path_mobile: str
    image_path_desktop: str | None
    link_url: str | None
    sort_order: int

    @field_validator("image_path_mobile")
    @classmethod
    def _to_url_mobile(cls, v: str) -> str:
        return media_url(v)

    @field_validator("image_path_desktop")
    @classmethod
    def _to_url_desktop(cls, v: str | None) -> str | None:
        return media_url(v) if v else None


class BannerUpdateSchema(BaseModel):
    """PATCH semantics — `link_url` is distinguished from "omitted" via
    `model_fields_set` in the endpoint, so it can be explicitly cleared."""

    link_url: str | None = None
    sort_order: int | None = None
