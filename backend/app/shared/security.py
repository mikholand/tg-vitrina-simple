from datetime import UTC, datetime, timedelta

import jwt
from pydantic import BaseModel

from app.core.config import Settings
from app.entities.user import UserRole


class TokenPayload(BaseModel):
    user_id: int
    role: UserRole


def create_jwt_token(payload: TokenPayload, settings: Settings) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.security.JWT_EXPIRE_MINUTES)
    claims = {
        "sub": str(payload.user_id),
        "role": payload.role.value,
        "exp": expire,
    }
    return jwt.encode(claims, settings.security.JWT_SECRET.get_secret_value(), algorithm="HS256")


def decode_jwt_token(token: str, settings: Settings) -> TokenPayload:
    claims = jwt.decode(token, settings.security.JWT_SECRET.get_secret_value(), algorithms=["HS256"])
    return TokenPayload(user_id=int(claims["sub"]), role=UserRole(claims["role"]))
