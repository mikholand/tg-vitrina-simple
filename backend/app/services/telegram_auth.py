from datetime import UTC, datetime, timedelta

import httpx
import jwt
from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.logging import get_logger
from app.dto.auth import TelegramWidgetLoginSchema
from app.entities.user import User, UserRole
from app.repositories.user import UserRepository
from app.shared.security import TokenPayload, create_jwt_token

logger = get_logger("services.telegram_auth")

INIT_DATA_MAX_AGE = timedelta(hours=24)

# Telegram's current Login Widget (https://core.telegram.org/bots/
# telegram-login) is OIDC-based: it hands the frontend a signed JWT
# ("id_token") instead of individually HMAC-signed fields. `aud` on that
# token is the bot's own numeric id (`Settings.telegram.bot_id`) and `iss`
# is always this fixed value — not configurable per bot.
TELEGRAM_OIDC_ISSUER = "https://oauth.telegram.org"
TELEGRAM_OIDC_JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"

class _HttpxPyJWKClient(PyJWKClient):
    """`PyJWKClient.fetch_data` fetches the JWKS over bare `urllib.request`,
    which does no response decompression at all — confirmed live,
    oauth.telegram.org's JWKS endpoint serves a gzip-encoded response
    regardless of what `Accept-Encoding` the client sends (or doesn't),
    and `json.load()` on the raw gzip bytes blows up with
    `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8b in position 1`
    — 0x8b is literally gzip's second magic byte. httpx decompresses
    transparently, so only the fetch step is overridden here; the kid
    matching and the in-memory JWKS cache (with its TTL) stay PyJWKClient's
    own unmodified logic."""

    def fetch_data(self) -> object:
        response = httpx.get(self.uri, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()


_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Module-level singleton rather than one per `TelegramAuthService`
    instance (which is request-scoped, see `app/di/providers.py`):
    `PyJWKClient` caches keys it has already fetched (by `kid`), so reusing
    one across requests means a JWKS round trip to Telegram only happens
    once per key, not once per login. A free function (not a class
    attribute) so tests can monkeypatch it to a fake client instead of
    making a real network call."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = _HttpxPyJWKClient(TELEGRAM_OIDC_JWKS_URL)
    return _jwks_client


class InvalidInitDataError(Exception):
    pass


class TelegramAuthService:
    def __init__(self, settings: Settings, user_repository: UserRepository) -> None:
        self._settings = settings
        self._user_repository = user_repository

    def _parse_init_data(self, init_data_raw: str) -> WebAppInitData:
        try:
            init_data = safe_parse_webapp_init_data(
                token=self._settings.telegram.BOT_TOKEN.get_secret_value(),
                init_data=init_data_raw,
            )
        except ValueError as exc:
            raise InvalidInitDataError("invalid_signature") from exc

        if init_data.auth_date is None or (
            datetime.now(UTC) - init_data.auth_date.replace(tzinfo=UTC) > INIT_DATA_MAX_AGE
        ):
            raise InvalidInitDataError("expired")
        if init_data.user is None:
            raise InvalidInitDataError("missing_user")
        return init_data

    async def login(self, init_data_raw: str) -> tuple[str, User]:
        if not init_data_raw:
            raise InvalidInitDataError("missing_init_data")

        init_data = self._parse_init_data(init_data_raw)
        tg_user = init_data.user
        assert tg_user is not None

        return await self._finish_login(
            user_id=tg_user.id,
            tg_username=tg_user.username,
            tg_first_name=tg_user.first_name,
            tg_last_name=tg_user.last_name,
            tg_photo_url=tg_user.photo_url,
        )

    def _verify_widget_id_token(self, id_token: str) -> dict:
        """Verifies Telegram's OIDC `id_token` and returns its claims. Unlike
        the Mini App's init_data (verified against our own bot token
        directly), this is a standard signed JWT verified against
        Telegram's own public keys — `PyJWKClient` looks up the right key by
        the token's `kid` header, then `jwt.decode` checks the signature
        plus `iss`/`aud`/`exp` (expiration is enforced by `jwt.decode`
        itself, so there's no separate freshness check to do here, unlike
        `_parse_init_data` above). Only RS256 is accepted — Telegram's
        documented default; a bot changed to a different algorithm under
        BotFather's Login Widget > Advanced would need this extended."""
        try:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(id_token)
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=TELEGRAM_OIDC_ISSUER,
                audience=str(self._settings.telegram.bot_id),
            )
        except jwt.PyJWTError as exc:
            # The client only ever sees the generic "invalid_signature" 401
            # below — logged here with the real exception so a rejected
            # login (wrong aud, expired, bad signature, JWKS fetch failure,
            # ...) is diagnosable from the logs instead of a dead end.
            logger.warning("widget_id_token_rejected", error=str(exc), error_type=type(exc).__name__)
            raise InvalidInitDataError("invalid_signature") from exc
        return claims

    async def login_via_widget(self, payload: TelegramWidgetLoginSchema) -> tuple[str, User]:
        """The plain-website login path (Telegram Login Widget), outside
        the Mini App — see `login()` above for the init_data path used
        there. Same upsert/promote/issue-token flow via `_finish_login`;
        only the signature check differs.

        The Telegram user id this app keys `User.id` on is the token's `id`
        claim, not its `sub` — `sub` is an opaque OIDC subject identifier
        (a long, unrelated number), while `id` is the same Telegram user id
        the Mini App's init_data carries. Using `sub` here would silently
        create a second, disconnected user record for the same person."""
        claims = self._verify_widget_id_token(payload.id_token)
        raw_id = claims.get("id")
        # Despite the unquoted `"id": 987654321` in Telegram's own example
        # token in the docs, a real token sends it as a numeric *string*
        # (confirmed live against alenazhao.ru) — same `str`-claim
        # convention OIDC already uses for `sub`/`aud`. Accept either.
        try:
            tg_user_id = int(raw_id) if raw_id is not None else None
        except (TypeError, ValueError):
            tg_user_id = None
        if tg_user_id is None:
            logger.warning("widget_id_token_missing_id_claim", claim_keys=list(claims.keys()))
            raise InvalidInitDataError("missing_user")

        return await self._finish_login(
            user_id=tg_user_id,
            tg_username=claims.get("preferred_username"),
            tg_first_name=claims.get("given_name") or claims.get("name") or "",
            tg_last_name=claims.get("family_name"),
            tg_photo_url=claims.get("picture"),
        )

    async def _finish_login(
        self,
        user_id: int,
        tg_username: str | None,
        tg_first_name: str | None,
        tg_last_name: str | None,
        tg_photo_url: str | None,
    ) -> tuple[str, User]:
        user = await self._user_repository.upsert_from_telegram(
            user_id=user_id,
            tg_username=tg_username,
            tg_first_name=tg_first_name,
            tg_last_name=tg_last_name,
            tg_photo_url=tg_photo_url,
        )

        if user_id in self._settings.security.super_admin_ids and user.role != UserRole.ADMIN:
            await self._user_repository.set_role(user.id, UserRole.ADMIN)
            user.role = UserRole.ADMIN

        token = create_jwt_token(TokenPayload(user_id=user.id, role=user.role), self._settings)
        return token, user
