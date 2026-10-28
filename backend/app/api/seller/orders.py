from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status

from app.api.deps import CurrentStaff
from app.dto.order import (
    OrderCustomerSchema,
    OrderItemSchema,
    OrderStatusUpdateSchema,
    SellerOrderSchema,
)
from app.entities.order import Order, OrderItem, OrderStatus
from app.entities.user import User
from app.repositories.order import OrderRepository
from app.repositories.user import UserRepository
from app.services.order import OrderService
from app.shared.pagination import Paginated

router = APIRouter(route_class=DishkaRoute, prefix="/seller/orders", tags=["seller"])


def _to_schema(order: Order, items: list[OrderItem], customer: User | None) -> SellerOrderSchema:
    schema = SellerOrderSchema.model_validate(order)
    schema.items = [OrderItemSchema.model_validate(item) for item in items]
    if customer is not None:
        schema.customer = OrderCustomerSchema.model_validate(customer)
    return schema


@router.get("")
async def list_orders(
    _: CurrentStaff,
    order_repository: FromDishka[OrderRepository],
    user_repository: FromDishka[UserRepository],
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    # Repeatable (`?status=accepted&status=shipped`) so the cabinet's
    # "В работе" filter is one request rather than one per status.
    status: list[OrderStatus] | None = Query(default=None),
) -> Paginated[SellerOrderSchema]:
    orders, total = await order_repository.list_for_seller(limit, offset, status)
    items_by_order = await order_repository.list_items_for_orders([o.id for o in orders])
    customers = await user_repository.get_many(
        list({o.customer_id for o in orders if o.customer_id is not None})
    )
    schemas = [
        _to_schema(
            order,
            items_by_order.get(order.id, []),
            customers.get(order.customer_id) if order.customer_id is not None else None,
        )
        for order in orders
    ]
    return Paginated[SellerOrderSchema](items=schemas, total=total, limit=limit, offset=offset)


@router.patch("/{order_id}/status")
async def change_order_status(
    order_id: int,
    payload: OrderStatusUpdateSchema,
    _: CurrentStaff,
    order_service: FromDishka[OrderService],
    order_repository: FromDishka[OrderRepository],
    user_repository: FromDishka[UserRepository],
) -> SellerOrderSchema:
    order = await order_service.change_status(order_id, payload.status)
    if order is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="order_not_found")
    items = await order_repository.list_items(order.id)
    customer = (
        await user_repository.get(order.customer_id) if order.customer_id is not None else None
    )
    return _to_schema(order, items, customer)
