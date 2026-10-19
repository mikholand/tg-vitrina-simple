from datetime import UTC, datetime, timedelta
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from app.api.deps import CurrentStaff
from app.repositories.product import ProductRepository
from app.repositories.view import ViewRepository

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/stats", tags=["seller"])

_PERIOD_DAYS = {"7d": 7, "30d": 30}


@router.get("")
async def get_stats(
    _: CurrentStaff,
    view_repository: FromDishka[ViewRepository],
    product_repository: FromDishka[ProductRepository],
    period: Annotated[str, Query(pattern="^(all|7d|30d)$")] = "all",
    top_limit: int = Query(default=10, le=50),
) -> dict:
    if period == "all":
        top_all_time = await product_repository.list_top_viewed(top_limit)
        return {
            "store_views_total": await view_repository.count_store_views(),
            "product_views_total": await view_repository.count_product_views_total(),
            "top_products": [
                {"id": p.id, "name": p.name, "views_total": p.views_total} for p in top_all_time
            ],
        }

    since_datetime = datetime.now(UTC) - timedelta(days=_PERIOD_DAYS[period])
    top_in_window = await view_repository.list_top_products_since(since_datetime, top_limit)
    return {
        "store_views_total": await view_repository.count_store_views_since(since_datetime.date()),
        "product_views_total": await view_repository.count_product_views_since(since_datetime),
        "top_products": [
            {"id": pid, "name": name, "views_total": views} for pid, name, views in top_in_window
        ],
    }
