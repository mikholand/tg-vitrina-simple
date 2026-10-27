from pydantic import BaseModel, ConfigDict

from app.entities.user import UserRole


class LoginResponseSchema(BaseModel):
    token: str
    user_id: int
    role: UserRole


class TelegramWidgetLoginSchema(BaseModel):
    """The payload Telegram's Login Widget callback hands the frontend
    verbatim — field names/types match
    https://core.telegram.org/widgets/login exactly, since
    `TelegramAuthService._verify_widget_hash` reconstructs Telegram's own
    data-check-string from these fields byte for byte."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class CurrentUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tg_username: str | None
    tg_first_name: str | None
    tg_last_name: str | None
    tg_photo_url: str | None
    role: UserRole
