from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.logging import get_logger
from app.dto.sync import IngestRawPostSchema
from app.entities.sync_state import SyncState, SyncStatus
from app.repositories.raw_post import RawPostRepository
from app.repositories.sync_state import SyncStateRepository

logger = get_logger(__name__)

# A full backfill pass only ever pulls the newest MAX_SYNC_POSTS posts off
# the channel, not its entire history — a seller onboarding a channel with
# years of posts doesn't actually want everything re-imported, and most of
# that volume would just get discarded further down the pipeline anyway.
# Fixed in SyncState.total_count once at the start of a fresh pass (see
# claim_job below) — same "set once, never touched again mid-pass or across
# a resume" convention already used for stop_id.
MAX_SYNC_POSTS = 100


class SyncOrchestrationService:
    """Owns the single application-wide sync checkpoint. There is no `Shop`
    to attach this to — one deployment, one channel, one sync state row.
    """

    def __init__(
        self,
        settings: Settings,
        sync_state_repository: SyncStateRepository,
        raw_post_repository: RawPostRepository,
    ) -> None:
        self._settings = settings
        self._sync_state_repository = sync_state_repository
        self._raw_post_repository = raw_post_repository

    async def get_status(self) -> SyncState:
        return await self._sync_state_repository.get()

    async def request_start(self, resume: bool = False) -> SyncState:
        return await self._sync_state_repository.request_sync(resume=resume)

    async def request_stop(self) -> SyncState:
        return await self._sync_state_repository.request_stop()

    # --- called by the userbot over the internal API -----------------------

    async def claim_job(self) -> SyncState | None:
        """Userbot polls this. If a sync was requested, transition it to
        RUNNING and fix `stop_id` for this pass (only on a fresh pass — a
        resumed/interrupted pass keeps its existing stop_id untouched)."""
        state = await self._sync_state_repository.get()
        if state.status != SyncStatus.REQUESTED:
            return None

        stop_id = state.stop_id
        if stop_id is None:
            stop_id = await self._raw_post_repository.get_max_message_id(
                self._settings.store.TELEGRAM_CHANNEL_ID
            ) or 0
        return await self._sync_state_repository.mark_running(stop_id, total_count=MAX_SYNC_POSTS)

    async def is_stop_requested(self) -> bool:
        state = await self._sync_state_repository.get()
        return state.stop_requested

    async def ingest_batch(self, posts: list[IngestRawPostSchema]) -> int:
        ingested = 0
        for post in posts:
            existing = await self._raw_post_repository.find_duplicate(
                post.channel_id, post.message_id, post.media_group_id
            )
            if existing is not None:
                if post.photo_paths:
                    await self._raw_post_repository.append_photos(existing, post.photo_paths)
                continue
            await self._raw_post_repository.create(
                channel_id=post.channel_id,
                message_id=post.message_id,
                media_group_id=post.media_group_id,
                raw_text=post.raw_text,
                photo_paths=post.photo_paths,
                posted_at=post.posted_at,
            )
            ingested += 1
        return ingested

    async def update_progress(
        self, done_count: int, total_count: int | None, cursor: int | None
    ) -> SyncState:
        state = await self._sync_state_repository.get()
        delta = max(done_count - state.done_count, 0)
        if cursor is not None:
            return await self._sync_state_repository.advance_cursor(cursor, delta, total_count)
        state.done_count = done_count
        if total_count is not None:
            state.total_count = total_count
        return state

    async def complete(self, success: bool, error: str | None, retry_after_seconds: int | None) -> SyncState:
        retry_at = None
        if not success and error != "sync_interrupted":
            delay = timedelta(seconds=retry_after_seconds) if retry_after_seconds else timedelta(minutes=10)
            retry_at = datetime.now(UTC) + delay
        state = await self._sync_state_repository.complete(success, error, retry_at)
        logger.info(
            "sync_pass_completed",
            success=success,
            error=error,
            status=state.status,
            retry_at=retry_at,
        )
        return state
