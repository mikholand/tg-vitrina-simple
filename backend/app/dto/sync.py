from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.entities.sync_state import SyncStatus


class SyncStateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: SyncStatus
    cursor: int | None
    stop_id: int | None
    done_count: int
    total_count: int | None
    attempts: int
    retry_at: datetime | None
    stop_requested: bool
    last_error: str | None
    updated_at: datetime


class IngestRawPostSchema(BaseModel):
    channel_id: int
    message_id: int
    media_group_id: int | None = None
    raw_text: str | None = None
    photo_paths: list[str] = []
    posted_at: datetime


class IngestBatchSchema(BaseModel):
    posts: list[IngestRawPostSchema]


class ProgressUpdateSchema(BaseModel):
    done_count: int
    total_count: int | None = None
    cursor: int | None = None


class CompleteSyncSchema(BaseModel):
    success: bool
    error: str | None = None
    retry_after_seconds: int | None = None
