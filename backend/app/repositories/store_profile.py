from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.entities.store_profile import STORE_PROFILE_SINGLETON_ID, StoreProfile


def _normalize_env_logo(logo: str | None) -> str | None:
    """`STORE_LOGO` in `.env` is documented/typically set as a host-relative
    URL like `/media/store/logo.png` (see .env.example), but the `logo`
    column — like every other media path in this codebase (see
    `save_store_logo`, `save_banner_image`) — stores a path *relative to
    MEDIA_ROOT* (e.g. `store/logo.png`), since `media_url()` always adds the
    `/media/` prefix itself. Strip it here so a fresh deployment doesn't end
    up with a double-prefixed, 404ing logo URL."""
    if logo is None:
        return None
    return logo.removeprefix("/media/").removeprefix("media/")


class StoreProfileRepository:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def get(self) -> StoreProfile:
        """Returns the singleton row, creating it from the `STORE_*` env
        vars on first access. Once created, env vars are no longer consulted
        — the DB row is the only source of truth from then on."""
        profile = await self._session.get(StoreProfile, STORE_PROFILE_SINGLETON_ID)
        if profile is None:
            profile = StoreProfile(
                id=STORE_PROFILE_SINGLETON_ID,
                name=self._settings.store.STORE_NAME,
                description=self._settings.store.STORE_DESCRIPTION,
                logo=_normalize_env_logo(self._settings.store.STORE_LOGO),
                contact_tg=self._settings.store.STORE_CONTACT_TG,
            )
            self._session.add(profile)
            await self._session.flush()
        return profile

    async def update(
        self,
        name: str | None = None,
        description: str | None = None,
        contact_tg: str | None = None,
    ) -> StoreProfile:
        profile = await self.get()
        if name is not None:
            profile.name = name
        if description is not None:
            profile.description = description
        if contact_tg is not None:
            profile.contact_tg = contact_tg
        await self._session.flush()
        return profile

    async def set_logo(self, logo_path: str) -> StoreProfile:
        profile = await self.get()
        profile.logo = logo_path
        await self._session.flush()
        return profile
