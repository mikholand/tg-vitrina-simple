from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, UploadFile

from app.api.deps import CurrentSeller
from app.core.config import Settings
from app.dto.store_profile import SellerSettingsSchema, StoreProfileUpdateSchema
from app.entities.store_profile import StoreProfile
from app.repositories.store_profile import StoreProfileRepository
from app.shared.media import media_url
from app.shared.uploads import save_store_logo

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/settings", tags=["seller"])


def _to_schema(profile: StoreProfile, settings: Settings) -> SellerSettingsSchema:
    return SellerSettingsSchema(
        store_name=profile.name,
        store_description=profile.description,
        store_logo=media_url(profile.logo) if profile.logo else None,
        store_contact_tg=profile.contact_tg,
        telegram_channel_id=settings.store.TELEGRAM_CHANNEL_ID,
        extractor_configured=settings.extractor.is_configured(),
    )


@router.get("")
async def get_settings(
    _: CurrentSeller,
    settings: FromDishka[Settings],
    store_profile_repository: FromDishka[StoreProfileRepository],
) -> SellerSettingsSchema:
    profile = await store_profile_repository.get()
    return _to_schema(profile, settings)


@router.patch("")
async def update_settings(
    payload: StoreProfileUpdateSchema,
    _: CurrentSeller,
    settings: FromDishka[Settings],
    store_profile_repository: FromDishka[StoreProfileRepository],
) -> SellerSettingsSchema:
    profile = await store_profile_repository.update(
        name=payload.name,
        description=payload.description,
        contact_tg=payload.contact_tg,
    )
    return _to_schema(profile, settings)


@router.post("/logo")
async def upload_logo(
    file: UploadFile,
    _: CurrentSeller,
    settings: FromDishka[Settings],
    store_profile_repository: FromDishka[StoreProfileRepository],
) -> SellerSettingsSchema:
    rel_path = await save_store_logo(settings, file)
    profile = await store_profile_repository.set_logo(rel_path)
    return _to_schema(profile, settings)
