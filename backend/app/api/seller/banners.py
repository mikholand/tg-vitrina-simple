from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import CurrentStaff
from app.core.config import Settings
from app.dto.banner import BannerSchema, BannerUpdateSchema
from app.repositories.banner import BannerLimitExceededError, BannerRepository
from app.shared.uploads import save_banner_image

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/banners", tags=["seller"])


@router.get("")
async def list_banners(
    _: CurrentStaff, banner_repository: FromDishka[BannerRepository]
) -> list[BannerSchema]:
    banners = await banner_repository.list_all()
    return [BannerSchema.model_validate(b) for b in banners]


@router.post("")
async def create_banner(
    file_mobile: UploadFile,
    file_desktop: UploadFile,
    _: CurrentStaff,
    settings: FromDishka[Settings],
    banner_repository: FromDishka[BannerRepository],
) -> BannerSchema:
    existing = await banner_repository.list_all()
    rel_path_mobile = await save_banner_image(settings, file_mobile)
    rel_path_desktop = await save_banner_image(settings, file_desktop)
    try:
        banner = await banner_repository.create(rel_path_mobile, rel_path_desktop, None, len(existing))
    except BannerLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BannerSchema.model_validate(banner)


@router.patch("/{banner_id}")
async def update_banner(
    banner_id: int,
    payload: BannerUpdateSchema,
    _: CurrentStaff,
    banner_repository: FromDishka[BannerRepository],
) -> BannerSchema:
    banner = await banner_repository.get(banner_id)
    if banner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="banner_not_found")
    banner = await banner_repository.update(
        banner,
        link_url=payload.link_url,
        link_url_set="link_url" in payload.model_fields_set,
        sort_order=payload.sort_order,
    )
    return BannerSchema.model_validate(banner)


@router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    banner_id: int,
    _: CurrentStaff,
    banner_repository: FromDishka[BannerRepository],
) -> None:
    banner = await banner_repository.get(banner_id)
    if banner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="banner_not_found")
    await banner_repository.delete(banner)
