from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import OptionalUser, VisitorKey
from app.clients.bot import BotClient
from app.dto.banner import BannerSchema
from app.dto.category import CategorySchema
from app.dto.contact import PublicContactSchema, contact_url
from app.dto.product import ProductSchema
from app.entities.contact import ContactType
from app.entities.product import Product
from app.repositories.banner import BannerRepository
from app.repositories.category import CategoryRepository
from app.repositories.contact import ContactRepository
from app.repositories.product import ProductRepository
from app.repositories.store_profile import StoreProfileRepository
from app.services.view import ViewService
from app.shared.media import media_url
from app.shared.pagination import Paginated

router = APIRouter(route_class=DishkaRoute, prefix="/catalog", tags=["catalog"])


def _to_schema(product: Product, category_ids: list[int]) -> ProductSchema:
    schema = ProductSchema.model_validate(product)
    schema.category_ids = category_ids
    return schema


@router.get("/store")
async def store_info(store_profile_repository: FromDishka[StoreProfileRepository]) -> dict:
    profile = await store_profile_repository.get()
    return {
        "name": profile.name,
        "description": profile.description,
        "logo": media_url(profile.logo) if profile.logo else None,
        "contact_tg": profile.contact_tg,
    }


@router.post("/visit", status_code=status.HTTP_204_NO_CONTENT)
async def record_visit(
    view_service: FromDishka[ViewService],
    user: OptionalUser,
    visitor_key: VisitorKey,
) -> None:
    if user is None and visitor_key is None:
        return
    await view_service.record_store_visit(user.id if user else None, visitor_key)


@router.get("/banners")
async def list_banners(
    banner_repository: FromDishka[BannerRepository],
) -> list[BannerSchema]:
    banners = await banner_repository.list_all()
    return [BannerSchema.model_validate(b) for b in banners]


@router.get("/contacts")
async def list_contacts(
    contact_repository: FromDishka[ContactRepository],
    store_profile_repository: FromDishka[StoreProfileRepository],
) -> list[PublicContactSchema]:
    """Кому покупатель может написать или позвонить.

    Пока продавец не завёл менеджеров, отдаём прежний `contact_tg`
    синтетической записью — иначе кнопка «Написать продавцу» пропала бы
    ровно там, где контакт указан, но список менеджеров ещё пуст.
    """
    contacts = await contact_repository.list_active()
    if contacts:
        return [
            PublicContactSchema(
                id=c.id, label=c.label, type=c.type, value=c.value, url=contact_url(c.type, c.value)
            )
            for c in contacts
        ]
    profile = await store_profile_repository.get()
    fallback = (profile.contact_tg or "").strip()
    if not fallback:
        return []
    return [
        PublicContactSchema(
            id=0,
            label="Продавец",
            type=ContactType.TELEGRAM,
            value=fallback,
            url=contact_url(ContactType.TELEGRAM, fallback),
        )
    ]


@router.get("/categories")
async def list_categories(
    category_repository: FromDishka[CategoryRepository],
) -> list[CategorySchema]:
    categories = await category_repository.list_all()
    return [CategorySchema.model_validate(c) for c in categories if not c.is_hidden]


@router.get("/products")
async def list_products(
    product_repository: FromDishka[ProductRepository],
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> Paginated[ProductSchema]:
    products, total = await product_repository.list_catalog(category_id, search, limit, offset)
    items = []
    for product in products:
        category_ids = await product_repository.get_category_ids(product.id)
        items.append(_to_schema(product, category_ids))
    return Paginated[ProductSchema](items=items, total=total, limit=limit, offset=offset)


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    product_repository: FromDishka[ProductRepository],
    view_service: FromDishka[ViewService],
    bot_client: FromDishka[BotClient],
    user: OptionalUser,
    visitor_key: VisitorKey,
) -> ProductSchema:
    product = await product_repository.get_published(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product_not_found")

    if user is not None or visitor_key is not None:
        await view_service.record_product_open(product_id, user.id if user else None, visitor_key)
        product.views_total += 1  # reflect the just-recorded view in the response

    category_ids = await product_repository.get_category_ids(product.id)
    schema = _to_schema(product, category_ids)
    schema.share_url = await bot_client.product_mini_app_url(product_id)
    return schema
