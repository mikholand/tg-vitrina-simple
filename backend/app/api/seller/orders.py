from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from app.api.deps import CurrentStaff
from app.dto.order import OrderItemSchema, OrderSchema
from app.entities.order import Order, OrderItem
from app.repositories.order import OrderRepository
from app.shared.pagination import Paginated

router = APIRouter(route_class=DishkaRoute, prefix="/seller/orders", tags=["seller"])


def _to_schema(order: Order, items: list[OrderItem]) -> OrderSchema:
    schema = OrderSchema.model_validate(order)
    schema.items = [OrderItemSchema.model_validate(item) for item in items]
    return schema


@router.get("")
async def list_orders(
    _: CurrentStaff,
    order_repository: FromDishka[OrderRepository],
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> Paginated[OrderSchema]:
    orders, total = await order_repository.list_for_seller(limit, offset)
    items_by_order = await order_repository.list_items_for_orders([o.id for o in orders])
    schemas = [_to_schema(order, items_by_order.get(order.id, [])) for order in orders]
    return Paginated[OrderSchema](items=schemas, total=total, limit=limit, offset=offset)
