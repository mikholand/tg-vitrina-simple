from datetime import datetime

from pydantic import BaseModel


class InviteSchema(BaseModel):
    """Текущая активная ссылка-приглашение в команду."""

    token: str
    #: Telegram Mini App deep link — `https://t.me/<bot>/<short>?startapp=<encoded>`,
    #: where `<encoded>` is `/invite/<token>` base64url-encoded (see
    #: `app/core/start_param.py`).
    url: str
    expires_at: datetime


class InviteRedeemSchema(BaseModel):
    token: str
