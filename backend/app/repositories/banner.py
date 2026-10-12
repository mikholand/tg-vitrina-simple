from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.banner import MAX_BANNERS, Banner


class BannerLimitExceededError(Exception):
    pass


class BannerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Banner]:
        result = await self._session.execute(select(Banner).order_by(Banner.sort_order, Banner.id))
        return list(result.scalars().all())

    async def get(self, banner_id: int) -> Banner | None:
        return await self._session.get(Banner, banner_id)

    async def create(self, image_path: str, link_url: str | None, sort_order: int) -> Banner:
        existing = await self.list_all()
        if len(existing) >= MAX_BANNERS:
            raise BannerLimitExceededError(f"at most {MAX_BANNERS} banners are allowed")
        banner = Banner(image_path=image_path, link_url=link_url, sort_order=sort_order)
        self._session.add(banner)
        await self._session.flush()
        return banner

    async def update(
        self,
        banner: Banner,
        link_url: str | None = None,
        link_url_set: bool = False,
        sort_order: int | None = None,
    ) -> Banner:
        if link_url_set:
            banner.link_url = link_url
        if sort_order is not None:
            banner.sort_order = sort_order
        await self._session.flush()
        return banner

    async def delete(self, banner: Banner) -> None:
        await self._session.delete(banner)
        await self._session.flush()
