from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.order import Order, OrderItem
from app.entities.product import Availability, Product


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def try_decrement_stock(self, product_id: int, quantity: int) -> bool:
        """Conditional `UPDATE ... WHERE quantity >= :quantity` — the
        standard pattern for decrementing a counter without a separate
        row lock: it only ever succeeds if enough stock is still there *at
        the moment the UPDATE runs*, so two concurrent checkouts racing for
        the last unit can't both succeed. Returns False (no rows matched)
        when there isn't enough left; the caller treats that exactly like
        the pre-check failing.

        Products with `quantity IS NULL` (stock not tracked at all) are
        never touched — nothing to decrement, always "available".
        """
        stmt = (
            update(Product)
            .where(
                Product.id == product_id,
                Product.quantity.is_not(None),
                Product.quantity >= quantity,
            )
            .values(quantity=Product.quantity - quantity)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return False

        # Sold out to exactly zero by this checkout — reads as "Нет в
        # наличии" from here on, quantity cleared back to untracked, same
        # rule `ProductService._normalize_stock` applies on a seller save
        # (there's nothing left to count until it's restocked). A follow-up
        # conditional UPDATE (rather than computing the post-decrement value
        # above) means this only ever fires when the row is *actually* at
        # zero right now, safe under concurrent decrements.
        await self._session.execute(
            update(Product)
            .where(Product.id == product_id, Product.quantity == 0)
            .values(availability=Availability.OUT_OF_STOCK, quantity=None)
            .execution_options(synchronize_session=False)
        )
        return True

    async def create(
        self,
        customer_id: int | None,
        total: Decimal,
        currency: str,
        comment: str | None,
        items: list[OrderItem],
        contact_name: str | None = None,
        contact_phone: str | None = None,
    ) -> Order:
        order = Order(
            customer_id=customer_id,
            total=total,
            currency=currency,
            comment=comment,
            contact_name=contact_name,
            contact_phone=contact_phone,
        )
        self._session.add(order)
        await self._session.flush()
        for item in items:
            item.order_id = order.id
            self._session.add(item)
        await self._session.flush()
        return order

    async def mark_notified(self, order_id: int) -> None:
        await self._session.execute(
            update(Order).where(Order.id == order_id).values(notified=True)
        )
        await self._session.flush()

    async def list_for_seller(self, limit: int, offset: int) -> tuple[list[Order], int]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        count_stmt = select(func.count()).select_from(Order)
        total = (await self._session.execute(count_stmt)).scalar_one()
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_items_for_orders(self, order_ids: list[int]) -> dict[int, list[OrderItem]]:
        if not order_ids:
            return {}
        result = await self._session.execute(
            select(OrderItem).where(OrderItem.order_id.in_(order_ids)).order_by(OrderItem.id)
        )
        grouped: dict[int, list[OrderItem]] = {order_id: [] for order_id in order_ids}
        for item in result.scalars().all():
            grouped[item.order_id].append(item)
        return grouped

    async def list_items(self, order_id: int) -> list[OrderItem]:
        grouped = await self.list_items_for_orders([order_id])
        return grouped.get(order_id, [])
