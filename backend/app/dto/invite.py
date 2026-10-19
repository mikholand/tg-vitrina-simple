from datetime import datetime

from pydantic import BaseModel


class InviteSchema(BaseModel):
    """Текущая активная ссылка-приглашение в команду."""

    token: str
    #: Telegram Mini App deep link — `https://t.me/<bot>?startapp=invite_<token>`.
    url: str
    expires_at: datetime


class InviteRedeemSchema(BaseModel):
    token: str
