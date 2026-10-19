import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.product import Product
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

    async def count_store_views_since(self, since: date) -> int:
        stmt = select(func.count(StoreView.id)).where(StoreView.view_date >= since)
        return (await self._session.scalar(stmt)) or 0

    async def count_product_views_total(self) -> int:
        """Every logged open, across all products, all time — the
        denominator shown next to `count_store_views()` on the "Всё время"
        statistics period (see `api/seller/stats.py`)."""
        stmt = select(func.count(ProductView.id))
        return (await self._session.scalar(stmt)) or 0

    async def count_product_views_since(self, since: datetime) -> int:
        stmt = select(func.count(ProductView.id)).where(ProductView.created_at >= since)
        return (await self._session.scalar(stmt)) or 0

    async def list_top_products_since(
        self, since: datetime, limit: int
    ) -> list[tuple[int, str, int]]:
        """Top products by view count within the window — unlike
        `ProductRepository.list_top_viewed`, which just sorts by the
        denormalized all-time `views_total` column, this counts rows from
        `product_views` directly so "7 дней"/"30 дней" periods only reflect
        views logged in that window."""
        views = func.count(ProductView.id)
        stmt = (
            select(Product.id, Product.name, views.label("views"))
            .join(ProductView, ProductView.product_id == Product.id)
            .where(ProductView.created_at >= since)
            .group_by(Product.id, Product.name)
            .order_by(views.desc(), Product.id)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], row[1], row[2]) for row in rows]
