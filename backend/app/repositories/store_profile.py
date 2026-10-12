from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.entities.store_profile import STORE_PROFILE_SINGLETON_ID, StoreProfile


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
                logo=self._settings.store.STORE_LOGO,
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
