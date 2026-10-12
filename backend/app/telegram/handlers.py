from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import Message
from dishka import AsyncContainer

from app.core.config import Settings
from app.core.logging import get_logger
from app.repositories.raw_post import RawPostRepository
from app.telegram.media_group import MediaGroupAggregator, PendingPost

logger = get_logger("telegram.channel_sync")


def build_channel_router(container: AsyncContainer, settings: Settings, bot: Bot) -> Router:
    router = Router(name="channel_sync")
    channel_id = settings.store.TELEGRAM_CHANNEL_ID

    async def persist(pending: PendingPost) -> None:
        await _persist_pending_post(container, settings, bot, pending)

    aggregator = MediaGroupAggregator(on_flush=persist)

    @router.channel_post()
    async def on_channel_post(message: Message) -> None:
        if message.chat.id != channel_id:
            return

        photo_file_id = message.photo[-1].file_id if message.photo else None
        text = message.caption or message.text

        await aggregator.add(
            channel_id=message.chat.id,
            message_id=message.message_id,
            media_group_id=int(message.media_group_id) if message.media_group_id else None,
            posted_at_ts=message.date.timestamp(),
            photo_file_id=photo_file_id,
            text=text,
        )

    return router


async def _persist_pending_post(
    container: AsyncContainer, settings: Settings, bot: Bot, pending: PendingPost
) -> None:
    from datetime import UTC, datetime

    rel_dir = f"raw_posts/{pending.channel_id}/{pending.message_id}"
    abs_dir = Path(settings.app.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    photo_paths: list[str] = []
    for index, file_id in enumerate(pending.photo_file_ids):
        rel_path = f"{rel_dir}/{index}.jpg"
        abs_path = Path(settings.app.MEDIA_ROOT) / rel_path
        await bot.download(file_id, destination=abs_path)
        photo_paths.append(rel_path)

    async with container() as request_container:
        raw_post_repository = await request_container.get(RawPostRepository)
        existing = await raw_post_repository.find_duplicate(
            pending.channel_id, pending.message_id, pending.media_group_id
        )
        if existing is not None:
            if photo_paths:
                await raw_post_repository.append_photos(existing, photo_paths)
            logger.info(
                "channel_post_duplicate_ignored",
                raw_post_id=existing.id,
                channel_id=pending.channel_id,
                message_id=pending.message_id,
            )
            return

        raw_post = await raw_post_repository.create(
            channel_id=pending.channel_id,
            message_id=pending.message_id,
            media_group_id=pending.media_group_id,
            raw_text=pending.text,
            photo_paths=photo_paths,
            posted_at=datetime.fromtimestamp(pending.posted_at_ts, tz=UTC),
        )
        logger.info(
            "channel_post_captured",
            raw_post_id=raw_post.id,
            channel_id=pending.channel_id,
            message_id=pending.message_id,
            photo_count=len(photo_paths),
        )
