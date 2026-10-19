from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.category import ProductCategory
from app.entities.product import Availability, Product, ProductStatus


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, product_id: int) -> Product | None:
        return await self._session.get(Product, product_id)

    async def get_by_source_post(self, raw_post_id: int) -> Product | None:
        stmt = select(Product).where(Product.source_post_id == raw_post_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def has_channel_message(self, channel_message_id: int) -> bool:
        stmt = select(Product.id).where(Product.channel_message_id == channel_message_id)
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None

    async def create_draft(
        self,
        name: str,
        price: Decimal | None,
        currency: str,
        description: str | None,
        sku: str | None,
        availability: Availability,
        quantity: int | None,
        photo_paths: list[str],
        source_post_id: int | None,
    ) -> Product:
        product = Product(
            name=name,
            price=price,
            currency=currency,
            description=description,
            sku=sku,
            availability=availability,
            quantity=quantity,
            photo_paths=photo_paths,
            status=ProductStatus.DRAFT,
            source_post_id=source_post_id,
        )
        self._session.add(product)
        await self._session.flush()
        return product

    async def set_categories(self, product_id: int, category_ids: list[int]) -> None:
        await self._session.execute(
            delete(ProductCategory).where(ProductCategory.product_id == product_id)
        )
        for category_id in category_ids:
            self._session.add(ProductCategory(product_id=product_id, category_id=category_id))
        await self._session.flush()

    async def get_category_ids(self, product_id: int) -> list[int]:
        stmt = select(ProductCategory.category_id).where(ProductCategory.product_id == product_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_seller(
        self, status: ProductStatus | None, search: str | None, limit: int, offset: int
    ) -> tuple[list[Product], int]:
        stmt = select(Product).order_by(Product.created_at.desc())
        count_stmt = select(func.count()).select_from(Product)
        if status is not None:
            stmt = stmt.where(Product.status == status)
            count_stmt = count_stmt.where(Product.status == status)
        if search:
            stmt = stmt.where(Product.name.ilike(f"%{search}%"))
            count_stmt = count_stmt.where(Product.name.ilike(f"%{search}%"))
        total = (await self._session.execute(count_stmt)).scalar_one()
        result = await self._session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def delete(self, product_id: int) -> None:
        """A plain row delete — ProductCategory/Favorite/View all reference
        products.id with ON DELETE CASCADE, and raw_posts.product_id with ON
        DELETE SET NULL, so everything downstream of the row is handled at
        the DB level without touching those tables here."""
        await self._session.execute(delete(Product).where(Product.id == product_id))

    async def list_catalog(
        self,
        category_id: int | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Product], int]:
        stmt = select(Product).where(Product.status == ProductStatus.PUBLISHED)
        count_stmt = select(func.count()).select_from(Product).where(
            Product.status == ProductStatus.PUBLISHED
        )

        if category_id is not None:
            stmt = stmt.join(ProductCategory, ProductCategory.product_id == Product.id).where(
                ProductCategory.category_id == category_id
            )
            count_stmt = count_stmt.join(
                ProductCategory, ProductCategory.product_id == Product.id
            ).where(ProductCategory.category_id == category_id)

        if search:
            stmt = stmt.where(Product.name.ilike(f"%{search}%"))
            count_stmt = count_stmt.where(Product.name.ilike(f"%{search}%"))

        stmt = stmt.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        total = (await self._session.execute(count_stmt)).scalar_one()
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_published(self, product_id: int) -> Product | None:
        stmt = select(Product).where(
            Product.id == product_id, Product.status == ProductStatus.PUBLISHED
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def increment_views(self, product_id: int) -> None:
        # synchronize_session=False: callers that hold an in-memory Product
        # instance for this id update its `views_total` themselves, since
        # the default "evaluate" sync would otherwise double-apply the +1.
        await self._session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(views_total=Product.views_total + 1)
            .execution_options(synchronize_session=False)
        )

    async def list_top_viewed(self, limit: int) -> list[Product]:
        stmt = select(Product).order_by(Product.views_total.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
