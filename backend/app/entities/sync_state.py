import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin

SYNC_STATE_SINGLETON_ID = 1


class SyncStatus(enum.StrEnum):
    IDLE = "idle"
    REQUESTED = "requested"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class SyncState(Base, TimestampMixin):
    """Singleton row (id=1) holding the userbot's resumable history-sync
    checkpoint for this application's one channel. There is no `shops` table
    to hang this off of — the deployment itself owns one sync state.
    """

    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=SYNC_STATE_SINGLETON_ID)
    status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, native_enum=False, length=20), default=SyncStatus.IDLE, nullable=False
    )
    # Oldest message_id successfully imported so far in the current/last pass.
    # Moves only after a batch is durably persisted. None = nothing imported yet.
    cursor: Mapped[int | None] = mapped_column(BigInteger)
    # Upper boundary fixed at the start of a pass (newest message_id already
    # known before this pass began). Never changes mid-pass.
    stop_id: Mapped[int | None] = mapped_column(BigInteger)
    done_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_count: Mapped[int | None] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(200))
