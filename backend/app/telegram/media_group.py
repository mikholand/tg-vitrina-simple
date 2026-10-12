import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

MEDIA_GROUP_DEBOUNCE_SECONDS = 1.5


@dataclass
class PendingPost:
    channel_id: int
    message_id: int
    media_group_id: int | None
    posted_at_ts: float
    photo_file_ids: list[str] = field(default_factory=list)
    text: str | None = None


class MediaGroupAggregator:
    """Buffers channel posts so a multi-photo album (several Telegram updates,
    one shared `media_group_id`) is flushed as a single post once no further
    update for that group has arrived for `MEDIA_GROUP_DEBOUNCE_SECONDS`.

    A lone message (no media_group_id) is flushed immediately.
    """

    def __init__(self, on_flush: Callable[[PendingPost], Awaitable[None]]) -> None:
        self._on_flush = on_flush
        self._pending: dict[str, PendingPost] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def _key(self, channel_id: int, media_group_id: int | None, message_id: int) -> str:
        return f"{channel_id}:{media_group_id}" if media_group_id else f"{channel_id}:msg:{message_id}"

    async def add(
        self,
        channel_id: int,
        message_id: int,
        media_group_id: int | None,
        posted_at_ts: float,
        photo_file_id: str | None,
        text: str | None,
    ) -> None:
        key = self._key(channel_id, media_group_id, message_id)
        pending = self._pending.get(key)
        if pending is None:
            pending = PendingPost(
                channel_id=channel_id,
                message_id=message_id,
                media_group_id=media_group_id,
                posted_at_ts=posted_at_ts,
            )
            self._pending[key] = pending
        if photo_file_id:
            pending.photo_file_ids.append(photo_file_id)
        if text:
            pending.text = text
        pending.message_id = min(pending.message_id, message_id)

        if media_group_id is None:
            await self._flush(key)
            return

        existing_task = self._tasks.get(key)
        if existing_task is not None:
            existing_task.cancel()
        self._tasks[key] = asyncio.create_task(self._flush_after_delay(key))

    async def _flush_after_delay(self, key: str) -> None:
        try:
            await asyncio.sleep(MEDIA_GROUP_DEBOUNCE_SECONDS)
        except asyncio.CancelledError:
            return
        await self._flush(key)

    async def _flush(self, key: str) -> None:
        pending = self._pending.pop(key, None)
        self._tasks.pop(key, None)
        if pending is None:
            return
        await self._on_flush(pending)
