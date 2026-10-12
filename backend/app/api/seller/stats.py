from datetime import UTC, datetime

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from app.api.deps import CurrentStaff
from app.repositories.product import ProductRepository
from app.repositories.view import ViewRepository

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/stats", tags=["seller"])


@router.get("")
async def get_stats(
    _: CurrentStaff,
    view_repository: FromDishka[ViewRepository],
    product_repository: FromDishka[ProductRepository],
    top_limit: int = Query(default=10, le=50),
) -> dict:
    today = datetime.now(UTC).date()
    top_products = await product_repository.list_top_viewed(top_limit)
    return {
        "store_views_total": await view_repository.count_store_views(),
        "store_views_today": await view_repository.count_store_views_on(today),
        "top_products": [
            {"id": p.id, "name": p.name, "views_total": p.views_total} for p in top_products
        ],
    }
