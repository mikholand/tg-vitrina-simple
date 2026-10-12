import uuid
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings
from app.entities.user import User, UserRole
from app.repositories.user import UserRepository
from app.shared.security import decode_jwt_token


@inject
async def get_current_user(
    settings: FromDishka[Settings],
    user_repository: FromDishka[UserRepository],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_jwt_token(token, settings)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from exc

    user = await user_repository.get(payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown_user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@inject
async def get_optional_user(
    settings: FromDishka[Settings],
    user_repository: FromDishka[UserRepository],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_jwt_token(token, settings)
    except Exception:
        return None
    return await user_repository.get(payload.user_id)


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_visitor_key(
    x_visitor_key: Annotated[str | None, Header()] = None,
) -> uuid.UUID | None:
    if not x_visitor_key:
        return None
    try:
        return uuid.UUID(x_visitor_key)
    except ValueError:
        return None


VisitorKey = Annotated[uuid.UUID | None, Depends(get_visitor_key)]


async def require_seller(user: CurrentUser) -> User:
    if user.role not in (UserRole.SELLER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="seller_access_required")
    return user


CurrentSeller = Annotated[User, Depends(require_seller)]


async def require_staff(user: CurrentUser) -> User:
    """Looser than `require_seller`: also allows moderators. Used by every
    seller-side endpoint except shop settings and moderator management
    themselves, which stay owner-only (`CurrentSeller`)."""
    if user.role not in (UserRole.SELLER, UserRole.ADMIN, UserRole.MODERATOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="staff_access_required")
    return user


CurrentStaff = Annotated[User, Depends(require_staff)]


@inject
async def require_internal_token(
    settings: FromDishka[Settings],
    x_internal_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.security.INTERNAL_API_TOKEN.get_secret_value()
    if not x_internal_token or x_internal_token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_internal_token")


RequireInternalToken = Annotated[None, Depends(require_internal_token)]
