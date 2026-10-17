from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentStaff
from app.dto.category import CategoryCreateSchema, CategorySchema, CategoryVisibilityUpdateSchema
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreateSchema,
    _: CurrentStaff,
    category_service: FromDishka[CategoryService],
) -> CategorySchema:
    try:
        category = await category_service.create(payload.name, payload.parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CategorySchema.model_validate(category)


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


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    _: CurrentStaff,
    category_repository: FromDishka[CategoryRepository],
    category_service: FromDishka[CategoryService],
) -> None:
    category = await category_repository.get(category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category_not_found")
    try:
        await category_service.delete(category_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
