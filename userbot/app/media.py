import asyncio
from pathlib import Path

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from app.logging import get_logger

logger = get_logger("userbot.media")

FLOOD_WAIT_SAFETY_MARGIN_SECONDS = 2
BASE_BACKOFF_SECONDS = 0.0
MAX_BACKOFF_SECONDS = 30.0
BACKOFF_GROWTH_FACTOR = 2.0
RELAX_STREAK_THRESHOLD = 5  # consecutive successes before easing the delay
MEDIA_FAILURE_LIMIT = 3  # give up on one photo after this many attempts


class AdaptiveMediaBackoff:
    """Grows the delay before each download after a failure, and relaxes it
    back down once a streak of successes has rebuilt confidence. This is
    separate from FLOOD_WAIT handling: FLOOD_WAIT is an exact, Telegram-
    mandated wait that is honored in full regardless of this backoff.
    """

    def __init__(self) -> None:
        self._delay = BASE_BACKOFF_SECONDS
        self._success_streak = 0

    async def wait(self) -> None:
        if self._delay > 0:
            await asyncio.sleep(self._delay)

    def record_success(self) -> None:
        self._success_streak += 1
        if self._success_streak >= RELAX_STREAK_THRESHOLD and self._delay > 0:
            self._delay = max(self._delay / BACKOFF_GROWTH_FACTOR, BASE_BACKOFF_SECONDS)
            self._success_streak = 0

    def record_failure(self) -> None:
        self._success_streak = 0
        self._delay = min(max(self._delay, 1.0) * BACKOFF_GROWTH_FACTOR, MAX_BACKOFF_SECONDS)


async def download_with_flood_wait(client: Client, message: Message, destination: Path) -> None:
    while True:
        try:
            await client.download_media(message, file_name=str(destination))
            return
        except FloodWait as exc:
            wait_seconds = exc.value + FLOOD_WAIT_SAFETY_MARGIN_SECONDS
            logger.warning("flood_wait", wait_seconds=wait_seconds, message_id=message.id)
            await asyncio.sleep(wait_seconds)


async def download_photo(
    client: Client,
    message: Message,
    destination: Path,
    backoff: AdaptiveMediaBackoff,
) -> bool:
    """Returns True if the photo was downloaded, False if it was given up on
    after `MEDIA_FAILURE_LIMIT` attempts — a single bad photo must never
    block the rest of the historical backfill.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, MEDIA_FAILURE_LIMIT + 1):
        await backoff.wait()
        try:
            await download_with_flood_wait(client, message, destination)

            # Pyrogram's download_media() can return normally (no exception)
            # while having written nothing: Client.handle_download() only
            # removes its *.temp file and returns None on a raised error —
            # if the underlying GetFile call comes back with an empty first
            # chunk (observed for some historical/archived messages, likely
            # a stale file reference that Telegram doesn't surface as a
            # hard error), the "" bytes are still written out as a real
            # 0-byte file at `destination`. Treat that the same as a
            # failed attempt instead of trusting "no exception" as success,
            # otherwise a permanently-broken empty file gets recorded in
            # photo_paths and silently 404s/renders broken in the frontend.
            if not destination.is_file() or destination.stat().st_size == 0:
                raise RuntimeError("downloaded file is empty")

            backoff.record_success()
            return True
        except Exception as exc:
            destination.unlink(missing_ok=True)
            backoff.record_failure()
            logger.warning(
                "media_download_failed",
                message_id=message.id,
                attempt=attempt,
                error=str(exc),
            )

    logger.error("media_download_abandoned", message_id=message.id)
    return False
