from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from app.api.deps import CurrentStaff
from app.dto.category import CategorySchema, CategoryVisibilityUpdateSchema
from app.repositories.category import CategoryRepository
from app.services.category import CategoryService

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/categories", tags=["seller"])


@router.get("")
async def list_categories(
    _: CurrentStaff, category_repository: FromDishka[CategoryRepository]
) -> list[CategorySchema]:
    categories = await category_repository.list_all()
    return [CategorySchema.model_validate(c) for c in categories]


@router.patch("/{category_id}/visibility")
async def set_visibility(
    category_id: int,
    payload: CategoryVisibilityUpdateSchema,
    _: CurrentStaff,
    category_repository: FromDishka[CategoryRepository],
    category_service: FromDishka[CategoryService],
) -> CategorySchema:
    await category_service.set_hidden(category_id, payload.is_hidden)
    category = await category_repository.get(category_id)
    return CategorySchema.model_validate(category)
