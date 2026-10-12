import uuid
from datetime import UTC, datetime

from app.repositories.product import ProductRepository
from app.repositories.view import ViewRepository


class ViewService:
    def __init__(self, view_repository: ViewRepository, product_repository: ProductRepository) -> None:
        self._view_repository = view_repository
        self._product_repository = product_repository

    async def record_store_visit(self, user_id: int | None, visitor_key: uuid.UUID | None) -> bool:
        today = datetime.now(UTC).date()
        return await self._view_repository.record_store_view(user_id, visitor_key, today)

    async def record_product_open(
        self, product_id: int, user_id: int | None, visitor_key: uuid.UUID | None
    ) -> None:
        """Every open counts — inserts the event and bumps views_total in
        the same unit of work (same session/transaction)."""
        await self._view_repository.record_product_view(product_id, user_id, visitor_key)
        await self._product_repository.increment_views(product_id)
