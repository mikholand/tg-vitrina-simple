from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.favorite import Favorite
from app.entities.product import Product


class FavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user_id: int, product_id: int) -> None:
        existing = await self._session.get(Favorite, (user_id, product_id))
        if existing is None:
            self._session.add(Favorite(user_id=user_id, product_id=product_id))
            await self._session.flush()

    async def remove(self, user_id: int, product_id: int) -> None:
        existing = await self._session.get(Favorite, (user_id, product_id))
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def list_product_ids(self, user_id: int) -> list[int]:
        result = await self._session.execute(
            select(Favorite.product_id).where(Favorite.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_products(self, user_id: int) -> list[Product]:
        stmt = select(Product).join(Favorite, Favorite.product_id == Product.id).where(
            Favorite.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def sync_from_client(self, user_id: int, product_ids: list[int]) -> None:
        """Merge a localStorage favorites list into the user's account on login."""
        existing = set(await self.list_product_ids(user_id))
        for product_id in product_ids:
            if product_id not in existing:
                self._session.add(Favorite(user_id=user_id, product_id=product_id))
        await self._session.flush()
