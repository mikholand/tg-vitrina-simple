from decimal import Decimal

from app.clients.bot import BotClient
from app.core.logging import get_logger
from app.entities.order import Order, OrderItem
from app.entities.user import User
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.store_profile import StoreProfileRepository

logger = get_logger("services.order")


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        store_profile_repository: StoreProfileRepository,
        bot_client: BotClient,
    ) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._store_profile_repository = store_profile_repository
        self._bot_client = bot_client

    async def checkout(
        self,
        customer: User | None,
        items: list[tuple[int, int]],
        comment: str | None,
        contact_name: str | None = None,
        contact_phone: str | None = None,
    ) -> Order:
        """Validates every line against the live catalog (never trusts a
        client-supplied price/name/status), reserves stock, snapshots the
        cart into an `Order` + `OrderItem`s, and forwards it to the seller's
        Telegram chat. Raises `ValueError` with a short machine-readable
        code on any validation failure — the API layer maps that straight
        to a 400 (see `app/api/catalog.py`).

        `customer` is `None` for a checkout from the plain website (outside
        the Telegram Mini App, so `OptionalUser` resolved no session) — in
        that case `contact_name`/`contact_phone` are the only way to know
        who the order is from, so they're required here rather than left to
        the DB's nullable columns to silently allow."""
        if not items:
            raise ValueError("empty_cart")

        if customer is None:
            contact_name = (contact_name or "").strip() or None
            contact_phone = (contact_phone or "").strip() or None
            if not contact_name or not contact_phone:
                raise ValueError("contact_required")

        # A client sending the same product twice (e.g. two rapid taps
        # before the cart store settles) shouldn't become two separate
        # stock-decrement attempts for the same product — merge by id first.
        merged: dict[int, int] = {}
        for product_id, quantity in items:
            merged[product_id] = merged.get(product_id, 0) + quantity

        # One query for every distinct product in the cart (`get_published_many`)
        # instead of one `SELECT` per line — checkout is a hot path, and a cart
        # with N distinct products used to cost N round trips here.
        products_by_id = {
            product.id: product
            for product in await self._product_repository.get_published_many(list(merged.keys()))
        }

        order_items: list[OrderItem] = []
        # Only products with tracked stock (`quantity IS NOT NULL`) need a
        # decrement at all — an untracked product is always "available" and
        # `try_decrement_stock` would otherwise report 0 rows matched for it
        # (its WHERE clause requires `quantity IS NOT NULL`), which looks
        # identical to "ran out" if not filtered out here.
        to_decrement: list[tuple[int, int]] = []
        total = Decimal("0")
        currency: str | None = None
        for product_id, quantity in merged.items():
            product = products_by_id.get(product_id)
            if product is None:
                raise ValueError(f"product_unavailable:{product_id}")
            if product.quantity is not None:
                if product.quantity < quantity:
                    raise ValueError(f"insufficient_stock:{product_id}")
                to_decrement.append((product_id, quantity))

            if product.price is None:
                # A seller can publish a product before setting a price
                # (nothing in ProductService ties publish to having one) —
                # silently charging 0 for it used to be possible here.
                raise ValueError(f"product_missing_price:{product_id}")
            if currency is None:
                currency = product.currency
            elif currency != product.currency:
                # Every product defaults to RUB and nothing in this single-
                # shop app currently lets a seller sell in more than one
                # currency, but the DTO doesn't enforce that — a cart mixing
                # two currencies used to just sum their prices together as
                # if they were the same money.
                raise ValueError("mixed_currencies")
            price = product.price
            total += price * quantity
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    sku=product.sku,
                    price=price,
                    currency=product.currency,
                    quantity=quantity,
                )
            )

        # Second pass, after every line has already passed the optimistic
        # check above: a conditional UPDATE per product guards against a
        # concurrent checkout that raced in between and took the last unit.
        for product_id, quantity in to_decrement:
            if not await self._order_repository.try_decrement_stock(product_id, quantity):
                raise ValueError(f"insufficient_stock:{product_id}")

        order = await self._order_repository.create(
            customer_id=customer.id if customer is not None else None,
            total=total,
            currency=currency or "RUB",  # merged is never empty here, so the loop above always ran
            comment=comment,
            items=order_items,
            contact_name=contact_name,
            contact_phone=contact_phone,
        )

        await self._notify(order, order_items, customer)
        return order

    async def _notify(self, order: Order, items: list[OrderItem], customer: User | None) -> None:
        profile = await self._store_profile_repository.get()
        chat_id = profile.order_notification_chat_id
        if chat_id is None:
            # Not configured yet (no admin has run `/setorderchat`) — the
            # order itself still goes through, just unannounced. The seller
            # order-history list is the fallback way to see it, and
            # `Order.notified` staying False is how that list flags it.
            logger.info("order_notification_skipped_no_chat", order_id=order.id)
            return

        text = self._format_notification(order, items, customer)
        try:
            await self._bot_client.notify_order(chat_id, text)
        except Exception:
            # A Telegram API hiccup (chat deleted, bot kicked, rate limit)
            # must never roll back an already-placed, stock-decremented
            # order — the customer already got their confirmation.
            logger.exception("order_notification_failed", order_id=order.id)
            return
        await self._order_repository.mark_notified(order.id)

    @staticmethod
    def _format_notification(order: Order, items: list[OrderItem], customer: User | None) -> str:
        if customer is not None:
            if customer.tg_username:
                who = f"@{customer.tg_username}"
            else:
                who = " ".join(
                    filter(None, [customer.tg_first_name, customer.tg_last_name])
                ) or str(customer.id)
        else:
            # Guest checkout from the plain website — `checkout()` already
            # guarantees `contact_name` is set whenever `customer` is None.
            who = order.contact_name or "гость с сайта"

        lines = [f"🛒 Новый заказ №{order.id} от {who}"]
        if order.contact_phone:
            lines.append(f"Телефон: {order.contact_phone}")
        for item in items:
            sku = f" ({item.sku})" if item.sku else ""
            lines.append(
                f"• {item.product_name}{sku} × {item.quantity} = {item.price * item.quantity} {item.currency}"
            )
        lines.append(f"Итого: {order.total} {order.currency}")
        if order.comment:
            lines.append(f"Комментарий: {order.comment}")
        return "\n".join(lines)
