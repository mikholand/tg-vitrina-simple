from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentSeller
from app.dto.moderator import ModeratorAddSchema, ModeratorSchema
from app.entities.user import UserRole
from app.repositories.user import UserRepository

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/moderators", tags=["seller"])

# Owner-only (CurrentSeller, not CurrentStaff) — this is the shop-settings-
# adjacent surface moderators must never reach themselves ("модератор без
# доступа к настройкам магазина").


@router.get("")
async def list_moderators(
    _: CurrentSeller, user_repository: FromDishka[UserRepository]
) -> list[ModeratorSchema]:
    moderators = await user_repository.list_by_role(UserRole.MODERATOR)
    return [ModeratorSchema.model_validate(m) for m in moderators]


@router.post("")
async def add_moderator(
    payload: ModeratorAddSchema,
    _: CurrentSeller,
    user_repository: FromDishka[UserRepository],
) -> ModeratorSchema:
    user = await user_repository.get(payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found_must_open_app_first",
        )
    if user.role in (UserRole.SELLER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_is_owner")
    await user_repository.set_role(user.id, UserRole.MODERATOR)
    return ModeratorSchema.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_moderator(
    user_id: int,
    _: CurrentSeller,
    user_repository: FromDishka[UserRepository],
) -> None:
    user = await user_repository.get(user_id)
    if user is None or user.role != UserRole.MODERATOR:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="moderator_not_found")
    await user_repository.set_role(user_id, UserRole.CUSTOMER)
