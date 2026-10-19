from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.dto.invite import InviteRedeemSchema
from app.dto.moderator import ModeratorSchema
from app.entities.user import UserRole
from app.repositories.invite import InviteRepository
from app.repositories.user import UserRepository

router = APIRouter(route_class=DishkaRoute, prefix="/invites", tags=["invites"])


@router.post("/redeem")
async def redeem_invite(
    payload: InviteRedeemSchema,
    user: CurrentUser,
    invite_repository: FromDishka[InviteRepository],
    user_repository: FromDishka[UserRepository],
) -> ModeratorSchema:
    # Validity (unused + not expired) is decided by `get_active()`'s own
    # SQL-side filter rather than comparing `invite.expires_at` against
    # `datetime.now()` here in Python — a value just read back from the DB
    # loses its tzinfo under SQLite, which would make that comparison raise
    # on an aware "now". Pushing the comparison into the query (where it's
    # just bind-parameter vs. stored string, both rendered the same way)
    # sidesteps that entirely, and happens to double as the "exactly one
    # link is ever live" check `InviteRepository.create()` relies on.
    invite = await invite_repository.get_by_token(payload.token)
    active = await invite_repository.get_active()
    if invite is None or active is None or active.id != invite.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invite_invalid_or_expired"
        )
    if user.role in (UserRole.SELLER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_is_owner")

    await invite_repository.mark_used(invite, user.id)
    if user.role != UserRole.MODERATOR:
        await user_repository.set_role(user.id, UserRole.MODERATOR)

    updated = await user_repository.get(user.id)
    assert updated is not None
    return ModeratorSchema.model_validate(updated)
