from datetime import UTC, datetime
from pathlib import Path

from pyrogram import Client

from app.backend_client import BackendClient, RawPostPayload, SyncJob
from app.history import PostGroup, fetch_batch, group_messages_into_posts
from app.logging import get_logger
from app.media import AdaptiveMediaBackoff, download_photo

logger = get_logger("userbot.sync_runner")


class SyncRunner:
    """Drives one backfill pass for a claimed `SyncJob`, walking strictly
    older messages from `job.cursor` (resuming) or `job.stop_id` (fresh
    start) until Pyrogram's history generator is naturally exhausted.
    """

    def __init__(
        self,
        client: Client,
        backend: BackendClient,
        channel_id: int,
        media_root: Path,
        batch_size: int,
    ) -> None:
        self._client = client
        self._backend = backend
        self._channel_id = channel_id
        self._media_root = media_root
        self._batch_size = batch_size

    async def run_pass(self, job: SyncJob) -> None:
        offset_id = job.cursor if job.cursor is not None else job.stop_id
        done_count = job.done_count
        backoff = AdaptiveMediaBackoff()

        try:
            while True:
                messages, next_offset_id, exhausted = await fetch_batch(
                    self._client, self._channel_id, offset_id, self._batch_size
                )

                if messages:
                    groups = group_messages_into_posts(messages)
                    payloads = [await self._build_payload(group, backoff) for group in groups]
                    await self._backend.ingest_batch(payloads)

                    done_count += len(groups)
                    cursor = min(g.message_id for g in groups)
                    await self._backend.update_progress(done_count, job.total_count, cursor)

                if exhausted:
                    await self._backend.complete(success=True, error=None)
                    return

                if await self._backend.is_stop_requested():
                    await self._backend.complete(success=False, error="sync_interrupted")
                    return

                offset_id = next_offset_id
        except Exception as exc:
            logger.error("sync_pass_failed", error=str(exc))
            await self._backend.complete(
                success=False, error=str(exc), retry_after_seconds=60
            )

    async def _build_payload(
        self, group: PostGroup, backoff: AdaptiveMediaBackoff
    ) -> RawPostPayload:
        photo_paths: list[str] = []
        for index, msg in enumerate(m for m in group.messages if m.photo):
            relative_path = (
                Path("raw_posts")
                / str(self._channel_id)
                / str(group.message_id)
                / f"{index}.jpg"
            )
            destination = self._media_root / relative_path
            # Store the path relative to MEDIA_ROOT, matching the convention
            # save_product_photo uses — the API layer (media_url()) prefixes
            # relative paths with /media/ when building URLs for the
            # frontend. Storing the absolute filesystem path here (which
            # already includes the /media root segment) would make that
            # prefixing double up to /media/media/...
            if await download_photo(self._client, msg, destination, backoff):
                photo_paths.append(str(relative_path))

        anchor = group.messages[0]
        return RawPostPayload(
            channel_id=self._channel_id,
            message_id=group.message_id,
            media_group_id=group.media_group_id,
            raw_text=group.text,
            photo_paths=photo_paths,
            posted_at=anchor.date or datetime.now(UTC),
        )
