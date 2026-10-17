from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.category import MAX_CATEGORY_DEPTH, Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, category_id: int) -> Category | None:
        return await self._session.get(Category, category_id)

    async def get_by_code(self, code: str) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.code == code))
        return result.scalars().first()

    async def list_all(self) -> list[Category]:
        result = await self._session.execute(select(Category).order_by(Category.depth, Category.sort_order))
        return list(result.scalars().all())

    async def get_fallback(self) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.is_fallback.is_(True)))
        return result.scalars().first()

    async def set_hidden(self, category_id: int, is_hidden: bool) -> None:
        category = await self.get(category_id)
        if category is not None:
            category.is_hidden = is_hidden
            await self._session.flush()

    async def create(
        self,
        name: str,
        code: str,
        parent_id: int | None,
        depth: int,
        sort_order: int = 0,
        is_fallback: bool = False,
    ) -> Category:
        if depth > MAX_CATEGORY_DEPTH:
            raise ValueError(f"category depth {depth} exceeds max {MAX_CATEGORY_DEPTH}")
        category = Category(
            name=name,
            code=code,
            parent_id=parent_id,
            depth=depth,
            sort_order=sort_order,
            is_fallback=is_fallback,
        )
        self._session.add(category)
        await self._session.flush()
        return category

    async def delete(self, category: Category) -> None:
        await self._session.delete(category)
        await self._session.flush()
