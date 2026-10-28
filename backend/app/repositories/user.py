from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.user import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_many(self, user_ids: list[int]) -> dict[int, User]:
        if not user_ids:
            return {}
        result = await self._session.execute(select(User).where(User.id.in_(user_ids)))
        return {user.id: user for user in result.scalars().all()}

    async def upsert_from_telegram(
        self,
        user_id: int,
        tg_username: str | None,
        tg_first_name: str | None,
        tg_last_name: str | None,
        tg_photo_url: str | None = None,
    ) -> User:
        user = await self.get(user_id)
        if user is None:
            user = User(
                id=user_id,
                tg_username=tg_username,
                tg_first_name=tg_first_name,
                tg_last_name=tg_last_name,
                tg_photo_url=tg_photo_url,
            )
            self._session.add(user)
        else:
            user.tg_username = tg_username
            user.tg_first_name = tg_first_name
            user.tg_last_name = tg_last_name
            user.tg_photo_url = tg_photo_url
        await self._session.flush()
        return user

    async def set_role(self, user_id: int, role: UserRole) -> None:
        user = await self.get(user_id)
        if user is not None:
            user.role = role
            await self._session.flush()

    async def list_by_role(self, role: UserRole) -> list[User]:
        result = await self._session.execute(select(User).where(User.role == role))
        return list(result.scalars().all())
