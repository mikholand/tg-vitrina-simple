from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.sync_state import SYNC_STATE_SINGLETON_ID, SyncState, SyncStatus


class SyncStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SyncState:
        state = await self._session.get(SyncState, SYNC_STATE_SINGLETON_ID)
        if state is None:
            state = SyncState(id=SYNC_STATE_SINGLETON_ID, status=SyncStatus.IDLE)
            self._session.add(state)
            await self._session.flush()
        return state

    async def request_sync(self, resume: bool) -> SyncState:
        """Flip to REQUESTED. If `resume` is False, the cursor/stop_id are
        cleared so the next pass starts a brand new walk from the newest
        message. If True, the existing cursor (if any) is kept so the
        userbot continues where it left off.
        """
        state = await self.get()
        state.status = SyncStatus.REQUESTED
        state.stop_requested = False
        if not resume:
            state.cursor = None
            state.stop_id = None
            state.done_count = 0
            state.total_count = None
            state.attempts = 0
        state.last_error = None
        await self._session.flush()
        return state

    async def request_stop(self) -> SyncState:
        state = await self.get()
        state.stop_requested = True
        await self._session.flush()
        return state

    async def mark_running(self, stop_id: int | None, total_count: int | None = None) -> SyncState:
        state = await self.get()
        state.status = SyncStatus.RUNNING
        # stop_id (and, alongside it, the post cap in total_count) are fixed
        # once at the start of a pass and never move again mid-pass — only
        # set them if this pass doesn't already have a stop_id (i.e. it's a
        # fresh pass, not a resume of an interrupted one). A resume keeps
        # walking toward the same cap it was given originally.
        if state.stop_id is None:
            state.stop_id = stop_id
            if total_count is not None:
                state.total_count = total_count
        await self._session.flush()
        return state

    async def advance_cursor(self, cursor: int, done_delta: int, total_count: int | None) -> SyncState:
        """Called only after a batch has been durably persisted. The cursor
        only ever moves toward older messages (downward)."""
        state = await self.get()
        if state.cursor is None or cursor < state.cursor:
            state.cursor = cursor
        state.done_count += done_delta
        if total_count is not None:
            state.total_count = total_count
        await self._session.flush()
        return state

    async def complete(
        self, success: bool, error: str | None, retry_at: datetime | None
    ) -> SyncState:
        state = await self.get()
        if success:
            state.status = SyncStatus.DONE
            state.cursor = None
            state.stop_id = None
            state.attempts = 0
            state.last_error = None
        elif error == "sync_interrupted":
            state.status = SyncStatus.INTERRUPTED
            state.last_error = None
        else:
            state.status = SyncStatus.FAILED
            state.attempts += 1
            state.last_error = error
            state.retry_at = retry_at
        state.stop_requested = False
        await self._session.flush()
        return state
