from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Query, UploadFile, status

from app.api.deps import CurrentStaff
from app.core.config import Settings
from app.dto.product import ProductCreateSchema, ProductSchema, ProductUpdateSchema
from app.entities.product import ProductStatus
from app.repositories.product import ProductRepository
from app.services.product import ProductService
from app.services.publishing import PublishingService
from app.shared.pagination import Paginated
from app.shared.uploads import save_product_photo, save_product_video

router = APIRouter(
    route_class=DishkaRoute,
    prefix="/seller/products", tags=["seller"])


def _to_schema(product, category_ids: list[int]) -> ProductSchema:
    schema = ProductSchema.model_validate(product)
    schema.category_ids = category_ids
    return schema


@router.get("")
async def list_products(
    _: CurrentStaff,
    product_repository: FromDishka[ProductRepository],
    status_filter: ProductStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> Paginated[ProductSchema]:
    products, total = await product_repository.list_seller(status_filter, q, limit, offset)
    items = [_to_schema(p, await product_repository.get_category_ids(p.id)) for p in products]
    return Paginated[ProductSchema](items=items, total=total, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateSchema,
    _: CurrentStaff,
    product_repository: FromDishka[ProductRepository],
    product_service: FromDishka[ProductService],
) -> ProductSchema:
    product = await product_service.create_by_seller(payload)
    return _to_schema(product, await product_repository.get_category_ids(product.id))


@router.get("/{product_id}")
async def get_product(
    product_id: int, _: CurrentStaff, product_repository: FromDishka[ProductRepository]
) -> ProductSchema:
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    return _to_schema(product, await product_repository.get_category_ids(product.id))


@router.patch("/{product_id}")
async def update_product(
    product_id: int,
    payload: ProductUpdateSchema,
    _: CurrentStaff,
    product_repository: FromDishka[ProductRepository],
    product_service: FromDishka[ProductService],
) -> ProductSchema:
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    product = await product_service.update_by_seller(product, payload)
    return _to_schema(product, await product_repository.get_category_ids(product.id))


@router.post("/{product_id}/photos")
async def upload_photo(
    product_id: int,
    file: UploadFile,
    _: CurrentStaff,
    settings: FromDishka[Settings],
    product_repository: FromDishka[ProductRepository],
) -> ProductSchema:
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    rel_path = await save_product_photo(settings, product_id, file)
    product.photo_paths = [*product.photo_paths, rel_path]
    return _to_schema(product, await product_repository.get_category_ids(product.id))


@router.post("/{product_id}/video")
async def upload_video(
    product_id: int,
    file: UploadFile,
    _: CurrentStaff,
    settings: FromDishka[Settings],
    product_repository: FromDishka[ProductRepository],
) -> ProductSchema:
    """One video per product — a second upload replaces whatever was there
    before (the old file is simply orphaned on disk, same tradeoff
    `save_store_logo` already makes for the store logo)."""
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    product.video_path = await save_product_video(settings, product_id, file)
    return _to_schema(product, await product_repository.get_category_ids(product.id))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    _: CurrentStaff,
    product_repository: FromDishka[ProductRepository],
    product_service: FromDishka[ProductService],
) -> None:
    """Delete a product permanently, media included. There is no undo — the
    seller confirms that in the dialog before this is ever called;
    `POST /{id}/hide` stays the reversible way to pull it off the storefront.
    """
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    await product_service.delete_product(product)


@router.post("/{product_id}/publish")
async def publish_product(
    product_id: int,
    _: CurrentStaff,
    product_repository: FromDishka[ProductRepository],
    product_service: FromDishka[ProductService],
    publishing_service: FromDishka[PublishingService],
) -> ProductSchema:
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    product = await product_service.set_status(product, ProductStatus.PUBLISHED)
    if product.publish_to_channel and product.channel_message_id is None:
        product.channel_message_id = await publishing_service.publish_to_channel(product)
    return _to_schema(product, await product_repository.get_category_ids(product.id))


@router.post("/{product_id}/hide")
async def hide_product(
    product_id: int,
    _: CurrentStaff,
    product_repository: FromDishka[ProductRepository],
    product_service: FromDishka[ProductService],
) -> ProductSchema:
    product = await product_repository.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")
    product = await product_service.set_status(product, ProductStatus.HIDDEN)
    return _to_schema(product, await product_repository.get_category_ids(product.id))
