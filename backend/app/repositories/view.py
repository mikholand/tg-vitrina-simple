import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.view import ProductView, StoreView


class ViewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_store_view(
        self, user_id: int | None, visitor_key: uuid.UUID | None, view_date: date
    ) -> bool:
        """Returns True if this is the visitor's first recorded view today."""
        stmt = select(StoreView.id).where(StoreView.view_date == view_date)
        stmt = stmt.where(StoreView.user_id == user_id) if user_id is not None else stmt.where(
            StoreView.visitor_key == visitor_key
        )
        existing = (await self._session.execute(stmt)).scalars().first()
        if existing is not None:
            return False
        self._session.add(StoreView(user_id=user_id, visitor_key=visitor_key, view_date=view_date))
        await self._session.flush()
        return True

    async def record_product_view(
        self, product_id: int, user_id: int | None, visitor_key: uuid.UUID | None
    ) -> None:
        """Every open is logged — no dedup. Caller must also bump
        `products.views_total` in the same transaction."""
        self._session.add(ProductView(product_id=product_id, user_id=user_id, visitor_key=visitor_key))
        await self._session.flush()

    async def count_product_views(self, product_id: int) -> int:
        stmt = select(ProductView.id).where(ProductView.product_id == product_id)
        return len((await self._session.execute(stmt)).scalars().all())

    async def count_store_views(self) -> int:
        return len((await self._session.execute(select(StoreView.id))).scalars().all())

    async def count_store_views_on(self, view_date: date) -> int:
        stmt = select(StoreView.id).where(StoreView.view_date == view_date)
        return len((await self._session.execute(stmt)).scalars().all())
