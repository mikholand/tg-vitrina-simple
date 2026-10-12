from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentSeller
from app.dto.raw_post import RawPostSchema
from app.entities.raw_post import RawPostStatus
from app.repositories.raw_post import RawPostRepository
from app.shared.pagination import Paginated

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/raw-posts", tags=["seller"])


@router.get("")
async def list_raw_posts(
    _: CurrentSeller,
    raw_post_repository: FromDishka[RawPostRepository],
    status_filter: RawPostStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> Paginated[RawPostSchema]:
    posts, total = await raw_post_repository.list_page(status_filter, limit, offset)
    items = [RawPostSchema.model_validate(p) for p in posts]
    return Paginated[RawPostSchema](items=items, total=total, limit=limit, offset=offset)


@router.get("/{raw_post_id}")
async def get_raw_post(
    raw_post_id: int, _: CurrentSeller, raw_post_repository: FromDishka[RawPostRepository]
) -> RawPostSchema:
    post = await raw_post_repository.get(raw_post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="raw_post_not_found")
    return RawPostSchema.model_validate(post)
