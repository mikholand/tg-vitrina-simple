from app.entities.product import Product
from app.repositories.favorite import FavoriteRepository


class FavoriteService:
    def __init__(self, favorite_repository: FavoriteRepository) -> None:
        self._favorite_repository = favorite_repository

    async def add(self, user_id: int, product_id: int) -> None:
        await self._favorite_repository.add(user_id, product_id)

    async def remove(self, user_id: int, product_id: int) -> None:
        await self._favorite_repository.remove(user_id, product_id)

    async def list_favorites(self, user_id: int) -> list[Product]:
        return await self._favorite_repository.list_products(user_id)

    async def merge_from_client(self, user_id: int, product_ids: list[int]) -> None:
        await self._favorite_repository.sync_from_client(user_id, product_ids)
