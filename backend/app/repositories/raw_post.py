from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.raw_post import RawPost, RawPostStatus


class RawPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_max_message_id(self, channel_id: int) -> int | None:
        """Newest message_id already known for this channel — used as the
        `stop_id` boundary so a fresh backfill pass stops exactly where the
        live bot's feed already took over, instead of re-importing it."""
        stmt = select(func.max(RawPost.message_id)).where(RawPost.channel_id == channel_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get(self, raw_post_id: int) -> RawPost | None:
        return await self._session.get(RawPost, raw_post_id)

    async def find_duplicate(
        self, channel_id: int, message_id: int, media_group_id: int | None
    ) -> RawPost | None:
        """One media group == one post == one RawPost. A lone message is
        identified by its own message_id. This is the dedup guard that
        backs the (Postgres-only) partial unique indexes created in the
        migration.
        """
        if media_group_id is not None:
            stmt = select(RawPost).where(
                RawPost.channel_id == channel_id, RawPost.media_group_id == media_group_id
            )
        else:
            stmt = select(RawPost).where(
                RawPost.channel_id == channel_id,
                RawPost.message_id == message_id,
                RawPost.media_group_id.is_(None),
            )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def append_photos(self, raw_post: RawPost, photo_paths: list[str]) -> None:
        raw_post.photo_paths = [*raw_post.photo_paths, *photo_paths]
        await self._session.flush()

    async def create(
        self,
        channel_id: int,
        message_id: int,
        media_group_id: int | None,
        raw_text: str | None,
        photo_paths: list[str],
        posted_at,
    ) -> RawPost:
        raw_post = RawPost(
            channel_id=channel_id,
            message_id=message_id,
            media_group_id=media_group_id,
            raw_text=raw_text,
            photo_paths=photo_paths,
            posted_at=posted_at,
            status=RawPostStatus.NEW,
        )
        self._session.add(raw_post)
        await self._session.flush()
        return raw_post

    async def claim_new_batch(self, limit: int) -> list[RawPost]:
        """Claim up to `limit` NEW posts for extraction, locking them so a
        second worker tick (or process) can't double-process the same rows.
        """
        stmt = (
            select(RawPost)
            .where(RawPost.status == RawPostStatus.NEW)
            .order_by(RawPost.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        posts = list(result.scalars().all())
        return posts

    async def mark_extracted(self, raw_post_id: int, product_id: int) -> None:
        raw_post = await self.get(raw_post_id)
        if raw_post is not None:
            raw_post.status = RawPostStatus.EXTRACTED
            raw_post.product_id = product_id
            await self._session.flush()

    async def mark_failed(self, raw_post_id: int) -> None:
        raw_post = await self.get(raw_post_id)
        if raw_post is not None:
            raw_post.status = RawPostStatus.FAILED
            await self._session.flush()

    async def list_page(
        self, status: RawPostStatus | None, limit: int, offset: int
    ) -> tuple[list[RawPost], int]:
        stmt = select(RawPost).order_by(RawPost.posted_at.desc())
        if status is not None:
            stmt = stmt.where(RawPost.status == status)
        count_stmt = select(RawPost.id)
        if status is not None:
            count_stmt = count_stmt.where(RawPost.status == status)
        total = len((await self._session.execute(count_stmt)).scalars().all())
        result = await self._session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all()), total
