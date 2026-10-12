from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.dto.product import ProductSchema
from app.services.favorite import FavoriteService

router = APIRouter(route_class=DishkaRoute, prefix="/favorites", tags=["favorites"])


class MergeFavoritesSchema(BaseModel):
    product_ids: list[int]


@router.get("")
async def list_favorites(
    user: CurrentUser, favorite_service: FromDishka[FavoriteService]
) -> list[ProductSchema]:
    products = await favorite_service.list_favorites(user.id)
    return [ProductSchema.model_validate(p) for p in products]


@router.put("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(
    product_id: int, user: CurrentUser, favorite_service: FromDishka[FavoriteService]
) -> None:
    await favorite_service.add(user.id, product_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: int, user: CurrentUser, favorite_service: FromDishka[FavoriteService]
) -> None:
    await favorite_service.remove(user.id, product_id)


@router.post("/merge", status_code=status.HTTP_204_NO_CONTENT)
async def merge_favorites(
    payload: MergeFavoritesSchema,
    user: CurrentUser,
    favorite_service: FromDishka[FavoriteService],
) -> None:
    """Called once on login to merge the anonymous localStorage favorites
    list into the user's account."""
    await favorite_service.merge_from_client(user.id, payload.product_ids)
