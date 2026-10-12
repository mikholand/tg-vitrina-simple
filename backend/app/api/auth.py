from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.dto.auth import CurrentUserSchema, LoginResponseSchema
from app.services.telegram_auth import InvalidInitDataError, TelegramAuthService

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/auth", tags=["auth"])


class LoginRequestSchema(BaseModel):
    init_data: str


@router.post("/telegram/login")
async def login(
    payload: LoginRequestSchema,
    auth_service: FromDishka[TelegramAuthService],
) -> LoginResponseSchema:
    try:
        token, user = await auth_service.login(payload.init_data)
    except InvalidInitDataError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return LoginResponseSchema(token=token, user_id=user.id, role=user.role)


@router.get("/me")
async def me(user: CurrentUser) -> CurrentUserSchema:
    return CurrentUserSchema.model_validate(user)
