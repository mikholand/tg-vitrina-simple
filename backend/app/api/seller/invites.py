from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from app.api.deps import CurrentSeller
from app.clients.bot import BotClient
from app.dto.invite import InviteSchema
from app.entities.invite import Invite
from app.repositories.invite import InviteRepository

router = APIRouter(route_class=DishkaRoute, prefix="/seller/invites", tags=["seller"])

# Owner-only (CurrentSeller, not CurrentStaff) — same tier as `moderators.py`,
# since generating an invite link is "shop settings adjacent" just like
# adding a moderator directly used to be.


async def _to_schema(invite: Invite, bot_client: BotClient) -> InviteSchema:
    username = await bot_client.username()
    return InviteSchema(
        token=invite.token,
        url=f"https://t.me/{username}?startapp=invite_{invite.token}",
        expires_at=invite.expires_at,
    )


@router.get("")
async def get_active_invite(
    _: CurrentSeller,
    invite_repository: FromDishka[InviteRepository],
    bot_client: FromDishka[BotClient],
) -> InviteSchema | None:
    invite = await invite_repository.get_active()
    if invite is None:
        return None
    return await _to_schema(invite, bot_client)


@router.post("")
async def create_invite(
    user: CurrentSeller,
    invite_repository: FromDishka[InviteRepository],
    bot_client: FromDishka[BotClient],
) -> InviteSchema:
    invite = await invite_repository.create(created_by=user.id)
    return await _to_schema(invite, bot_client)
