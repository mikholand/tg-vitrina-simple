import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.invite import Invite

INVITE_TTL = timedelta(days=7)


class InviteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, created_by: int) -> Invite:
        # Sharing a "new" link should supersede whatever link was shared
        # before it — otherwise an old link someone already has stays valid
        # forever, which defeats the point of a one-time invite.
        await self._session.execute(
            update(Invite).where(Invite.used_by.is_(None)).values(expires_at=datetime.now(UTC))
        )
        invite = Invite(
            token=secrets.token_urlsafe(24),
            created_by=created_by,
            expires_at=datetime.now(UTC) + INVITE_TTL,
        )
        self._session.add(invite)
        await self._session.flush()
        return invite

    async def get_active(self) -> Invite | None:
        result = await self._session.execute(
            select(Invite)
            .where(Invite.used_by.is_(None), Invite.expires_at > datetime.now(UTC))
            .order_by(Invite.id.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_by_token(self, token: str) -> Invite | None:
        result = await self._session.execute(select(Invite).where(Invite.token == token))
        return result.scalars().first()

    async def mark_used(self, invite: Invite, user_id: int) -> Invite:
        invite.used_by = user_id
        invite.used_at = datetime.now(UTC)
        await self._session.flush()
        return invite
