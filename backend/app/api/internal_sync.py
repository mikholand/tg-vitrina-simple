from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status

from app.api.deps import require_internal_token
from app.core.config import Settings
from app.dto.sync import (
    CompleteSyncSchema,
    IngestBatchSchema,
    ProgressUpdateSchema,
    SyncStateSchema,
)
from app.services.sync import SyncOrchestrationService

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/internal/sync", tags=["internal"], dependencies=[Depends(require_internal_token)]
)


@router.get("/channel")
async def channel_info(settings: FromDishka[Settings]) -> dict[str, int]:
    return {"channel_id": settings.store.TELEGRAM_CHANNEL_ID}


@router.get("/job")
async def claim_job(
    sync_service: FromDishka[SyncOrchestrationService],
) -> SyncStateSchema | None:
    state = await sync_service.claim_job()
    return SyncStateSchema.model_validate(state) if state else None


@router.get("/stop-requested")
async def stop_requested(sync_service: FromDishka[SyncOrchestrationService]) -> dict[str, bool]:
    return {"stop_requested": await sync_service.is_stop_requested()}


@router.post("/ingest")
async def ingest(
    payload: IngestBatchSchema,
    sync_service: FromDishka[SyncOrchestrationService],
) -> dict[str, int]:
    ingested = await sync_service.ingest_batch(payload.posts)
    return {"ingested": ingested}


@router.post("/progress", status_code=status.HTTP_204_NO_CONTENT)
async def progress(
    payload: ProgressUpdateSchema,
    sync_service: FromDishka[SyncOrchestrationService],
) -> None:
    await sync_service.update_progress(payload.done_count, payload.total_count, payload.cursor)


@router.post("/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete(
    payload: CompleteSyncSchema,
    sync_service: FromDishka[SyncOrchestrationService],
) -> None:
    await sync_service.complete(payload.success, payload.error, payload.retry_after_seconds)
