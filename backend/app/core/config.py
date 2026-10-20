from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class StoreSettings(BaseSettings):
    """Static configuration of the single store this deployment serves."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    STORE_NAME: str = "Shop"
    STORE_DESCRIPTION: str = ""
    STORE_LOGO: str | None = None
    STORE_CONTACT_TG: str | None = None
    TELEGRAM_CHANNEL_ID: int


class TelegramSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BOT_TOKEN: SecretStr


class UserbotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    USERBOT_API_ID: int = 0
    USERBOT_API_HASH: str = ""
    USERBOT_SESSION: str = ""
    USERBOT_IPV6: bool = False
    USERBOT_POLL_INTERVAL: int = 10


class ExtractorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENROUTER_API_KEY: SecretStr | None = None
    OPENROUTER_MODEL: str = "mistralai/mistral-7b-instruct"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    EXTRACTOR_POLL_INTERVAL: int = 15
    EXTRACTOR_MAX_RETRIES: int = 2
    EXTRACTOR_BATCH_SIZE: int = 10
    EXTRACTOR_CONCURRENCY: int = 3

    def is_configured(self) -> bool:
        return self.OPENROUTER_API_KEY is not None


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "vitrina"
    POSTGRES_PASSWORD: str = "vitrina"
    POSTGRES_DB: str = "vitrina"

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    JWT_SECRET: SecretStr = SecretStr("change_me")
    JWT_EXPIRE_MINUTES: int = 43200
    SUPER_ADMIN_IDS: str = ""
    INTERNAL_API_TOKEN: SecretStr = SecretStr("change_me_internal_token")

    @property
    def super_admin_ids(self) -> set[int]:
        return {int(v) for v in self.SUPER_ADMIN_IDS.split(",") if v.strip()}


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MEDIA_ROOT: str = "/media"
    LOG_LEVEL: str = "INFO"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"
    # Public HTTPS URL of the storefront Mini App, used to build the "Open
    # shop" WebApp button the bot sends in reply to /start. Telegram requires
    # WebApp button URLs to be https, so this is left unset (button omitted)
    # rather than defaulting to something like http://localhost.
    WEBAPP_URL: str = ""
    # Short name of the Mini App's Direct Link, set up once in @BotFather
    # ("Bot Settings → Mini App → Direct Links → Create Direct Link"). A bare
    # `https://t.me/<bot>?startapp=...` link does NOT launch the Mini App
    # unless the bot's default Menu Button is itself a Web App — it just
    # opens the bot's chat. A Direct Link does launch it, but only via
    # `https://t.me/<bot>/<short_name>?startapp=...` — the short name must be
    # in the URL. "menu" matches this deployment's existing Direct Link;
    # override via env if it's ever renamed in BotFather.
    MINI_APP_SHORT_NAME: str = "menu"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


class Settings:
    def __init__(self) -> None:
        self.store = StoreSettings()
        self.telegram = TelegramSettings()
        self.userbot = UserbotSettings()
        self.extractor = ExtractorSettings()
        self.db = DatabaseSettings()
        self.security = SecuritySettings()
        self.app = AppSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
