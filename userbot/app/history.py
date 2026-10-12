import asyncio
from dataclasses import dataclass, field

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from app.logging import get_logger

logger = get_logger("userbot.history")

FLOOD_WAIT_SAFETY_MARGIN_SECONDS = 2
LOOKAHEAD_MARGIN = 50  # comfortably larger than Telegram's max album size (10)


@dataclass
class PostGroup:
    media_group_id: int | None
    messages: list[Message] = field(default_factory=list)

    @property
    def message_id(self) -> int:
        return min(m.id for m in self.messages)

    @property
    def text(self) -> str | None:
        for m in self.messages:
            if m.caption or m.text:
                return m.caption or m.text
        return None


async def fetch_batch(
    client: Client, chat_id: int, offset_id: int, batch_size: int
) -> tuple[list[Message], int | None, bool]:
    """Fetches the next `batch_size` messages older than `offset_id`, but
    never cuts a media group in half — if the batch boundary lands inside
    an album, it is extended until the album's messages are all included.

    Returns (messages, next_offset_id, exhausted). `next_offset_id` is the
    offset to pass on the following call; `exhausted` is True once the
    channel's beginning has been reached (no history left to backfill).
    """
    messages: list[Message] = []

    while True:
        try:
            async for msg in client.get_chat_history(
                chat_id, offset_id=offset_id, limit=batch_size + LOOKAHEAD_MARGIN
            ):
                if len(messages) >= batch_size:
                    last = messages[-1]
                    if last.media_group_id is None or msg.media_group_id != last.media_group_id:
                        return messages, msg.id + 1, False
                messages.append(msg)
            return messages, None, True
        except FloodWait as exc:
            wait_seconds = exc.value + FLOOD_WAIT_SAFETY_MARGIN_SECONDS
            logger.warning("flood_wait", wait_seconds=wait_seconds, offset_id=offset_id)
            # Retry the whole page fetch — any messages collected before the
            # flood wait are discarded since Pyrogram's async generator
            # cannot be resumed mid-page.
            messages = []
            await asyncio.sleep(wait_seconds)


def group_messages_into_posts(messages: list[Message]) -> list[PostGroup]:
    """Messages arrive newest-first; an album's messages are contiguous, so
    a simple run-length grouping by `media_group_id` is sufficient."""
    groups: list[PostGroup] = []
    current: PostGroup | None = None

    for msg in messages:
        if (
            current is not None
            and msg.media_group_id is not None
            and msg.media_group_id == current.media_group_id
        ):
            current.messages.append(msg)
        else:
            current = PostGroup(media_group_id=msg.media_group_id, messages=[msg])
            groups.append(current)

    return groups
