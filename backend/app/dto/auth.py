from pydantic import BaseModel, ConfigDict

from app.entities.user import UserRole


class LoginResponseSchema(BaseModel):
    token: str
    user_id: int
    role: UserRole


class TelegramWidgetLoginSchema(BaseModel):
    """Telegram's current Login Widget (https://core.telegram.org/bots/
    telegram-login — the legacy HMAC-signed-fields widget this replaced is
    archived at /widgets/login-legacy and no longer accepts logins for a
    bot whose domain was registered through @BotFather's newer "Login
    Widget" panel, which is OIDC-based) hands the frontend a signed JWT
    rather than individual fields — everything (id, name, username, photo)
    comes from its verified claims instead, see
    `TelegramAuthService._verify_widget_id_token`."""

    id_token: str


class CurrentUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tg_username: str | None
    tg_first_name: str | None
    tg_last_name: str | None
    tg_photo_url: str | None
    role: UserRole
