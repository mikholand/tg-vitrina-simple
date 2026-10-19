from pydantic import BaseModel, ConfigDict

from app.entities.user import UserRole


class LoginResponseSchema(BaseModel):
    token: str
    user_id: int
    role: UserRole


class CurrentUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tg_username: str | None
    tg_first_name: str | None
    tg_last_name: str | None
    tg_photo_url: str | None
    role: UserRole
