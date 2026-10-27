import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data

from app.core.config import Settings
from app.dto.auth import TelegramWidgetLoginSchema
from app.entities.user import User, UserRole
from app.repositories.user import UserRepository
from app.shared.security import TokenPayload, create_jwt_token

INIT_DATA_MAX_AGE = timedelta(hours=24)


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

    def _verify_widget_hash(self, payload: TelegramWidgetLoginSchema) -> None:
        """Telegram's Login Widget signs its payload differently from the
        Mini App's init_data (`_parse_init_data` above, verified by aiogram
        against the raw bot token): HMAC-SHA256 over the sorted
        "key=value" fields, keyed by SHA256(bot_token) rather than the
        token itself — see
        https://core.telegram.org/widgets/login#checking-authorization."""
        fields = payload.model_dump(exclude={"hash"}, exclude_none=True)
        data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
        secret_key = hashlib.sha256(
            self._settings.telegram.BOT_TOKEN.get_secret_value().encode()
        ).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed_hash, payload.hash):
            raise InvalidInitDataError("invalid_signature")

        auth_date = datetime.fromtimestamp(payload.auth_date, tz=UTC)
        if datetime.now(UTC) - auth_date > INIT_DATA_MAX_AGE:
            raise InvalidInitDataError("expired")

    async def login_via_widget(self, payload: TelegramWidgetLoginSchema) -> tuple[str, User]:
        """The plain-website login path (Telegram Login Widget), outside
        the Mini App — see `login()` above for the init_data path used
        there. Same upsert/promote/issue-token flow via `_finish_login`;
        only the signature check differs."""
        self._verify_widget_hash(payload)
        return await self._finish_login(
            user_id=payload.id,
            tg_username=payload.username,
            tg_first_name=payload.first_name,
            tg_last_name=payload.last_name,
            tg_photo_url=payload.photo_url,
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
