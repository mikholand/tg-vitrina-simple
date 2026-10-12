from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from app.api.deps import CurrentSeller
from app.dto.sync import SyncStateSchema
from app.services.sync import SyncOrchestrationService

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/sync", tags=["seller"])


@router.get("")
async def get_sync_status(
    _: CurrentSeller, sync_service: FromDishka[SyncOrchestrationService]
) -> SyncStateSchema:
    state = await sync_service.get_status()
    return SyncStateSchema.model_validate(state)


@router.post("/start")
async def start_sync(
    _: CurrentSeller,
    sync_service: FromDishka[SyncOrchestrationService],
    resume: bool = False,
) -> SyncStateSchema:
    state = await sync_service.request_start(resume=resume)
    return SyncStateSchema.model_validate(state)


@router.post("/stop")
async def stop_sync(
    _: CurrentSeller, sync_service: FromDishka[SyncOrchestrationService]
) -> SyncStateSchema:
    state = await sync_service.request_stop()
    return SyncStateSchema.model_validate(state)
