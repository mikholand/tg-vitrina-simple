from datetime import UTC, datetime, timedelta

from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data

from app.core.config import Settings
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

        user = await self._user_repository.upsert_from_telegram(
            user_id=tg_user.id,
            tg_username=tg_user.username,
            tg_first_name=tg_user.first_name,
            tg_last_name=tg_user.last_name,
        )

        if tg_user.id in self._settings.security.super_admin_ids and user.role != UserRole.ADMIN:
            await self._user_repository.set_role(user.id, UserRole.ADMIN)
            user.role = UserRole.ADMIN

        token = create_jwt_token(TokenPayload(user_id=user.id, role=user.role), self._settings)
        return token, user
