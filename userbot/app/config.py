from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """This process owns no store configuration of its own — the channel id
    and everything else store-specific is fetched from the backend's
    internal API. Only userbot-local connection details live here.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    USERBOT_API_ID: int
    USERBOT_API_HASH: str
    USERBOT_SESSION: str
    USERBOT_IPV6: bool = False
    USERBOT_POLL_INTERVAL: int = 10
    USERBOT_BATCH_SIZE: int = 10

    BACKEND_INTERNAL_URL: str = "http://backend:8000/api/v1/internal/sync"
    INTERNAL_API_TOKEN: str = "change_me_internal_token"

    MEDIA_ROOT: str = "/media"
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
