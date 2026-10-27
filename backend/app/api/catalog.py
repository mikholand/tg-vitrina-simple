from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response

from app.api.deps import CurrentUser, OptionalUser, VisitorKey
from app.clients.bot import BotClient
from app.core.config import Settings
from app.dto.banner import BannerSchema
from app.dto.category import CategorySchema
from app.dto.contact import PublicContactSchema, contact_url
from app.dto.order import CheckoutRequestSchema, OrderItemSchema, OrderSchema
from app.dto.product import ProductSchema
from app.entities.contact import ContactType
from app.entities.order import Order, OrderItem
from app.entities.product import Product
from app.repositories.banner import BannerRepository
from app.repositories.category import CategoryRepository
from app.repositories.contact import ContactRepository
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.store_profile import StoreProfileRepository
from app.services.order import OrderService
from app.services.view import ViewService
from app.shared.media import media_url
from app.shared.pagination import Paginated

router = APIRouter(route_class=DishkaRoute, prefix="/catalog", tags=["catalog"])


def _to_schema(product: Product, category_ids: list[int]) -> ProductSchema:
    schema = ProductSchema.model_validate(product)
    schema.category_ids = category_ids
    return schema


def _order_to_schema(order: Order, items: list[OrderItem]) -> OrderSchema:
    schema = OrderSchema.model_validate(order)
    schema.items = [OrderItemSchema.model_validate(item) for item in items]
    return schema


@router.get("/store")
async def store_info(
    store_profile_repository: FromDishka[StoreProfileRepository],
    settings: FromDishka[Settings],
) -> dict:
    profile = await store_profile_repository.get()
    return {
        "name": profile.name,
        "description": profile.description,
        "logo": media_url(profile.logo) if profile.logo else None,
        "contact_tg": profile.contact_tg,
        # Lets the plain website render Telegram's Login Widget
        # (data-client-id) without a build-time env var — see
        # `shared/telegram/widget.ts` on the frontend. This is the bot's
        # numeric id, same value as the OIDC `client_id`/`aud` the backend
        # itself checks in TelegramAuthService._verify_widget_id_token.
        "bot_client_id": settings.telegram.bot_id,
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
    category_ids_by_product = await product_repository.get_category_ids_many(
        [p.id for p in products]
    )
    items = [
        _to_schema(product, category_ids_by_product.get(product.id, [])) for product in products
    ]
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


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutRequestSchema,
    user: OptionalUser,
    order_service: FromDishka[OrderService],
    order_repository: FromDishka[OrderRepository],
) -> OrderSchema:
    try:
        order = await order_service.checkout(
            user,
            [(item.product_id, item.quantity) for item in payload.items],
            payload.comment,
            payload.contact_name,
            payload.contact_phone,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    items = await order_repository.list_items(order.id)
    return _order_to_schema(order, items)


@router.get("/orders/my")
async def list_my_orders(
    user: CurrentUser,
    order_repository: FromDishka[OrderRepository],
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> Paginated[OrderSchema]:
    """A logged-in customer's own order history (Mini App or the website
    Login Widget — `CurrentUser`, not `OptionalUser`: there's nothing to
    list for a guest checkout, which has no verified identity to match
    against). Guest orders (`customer_id IS NULL`) never show up here, by
    design — see `OrderRepository.list_for_customer`."""
    orders, total = await order_repository.list_for_customer(user.id, limit, offset)
    items_by_order = await order_repository.list_items_for_orders([o.id for o in orders])
    schemas = [_order_to_schema(order, items_by_order.get(order.id, [])) for order in orders]
    return Paginated[OrderSchema](items=schemas, total=total, limit=limit, offset=offset)


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt(settings: FromDishka[Settings]) -> str:
    """Served at the site root (see `frontend/nginx.conf`'s `/robots.txt`
    proxy_pass) rather than as a static frontend file, so the `Sitemap:`
    line always points at whatever domain this deployment is actually
    configured for (`WEBAPP_URL`) instead of a hardcoded value baked into
    the repo. `/seller`, `/cart`, `/favorites` are purely personal/staff
    screens — nothing there is worth a search engine's crawl budget, and
    `/seller/*` isn't reachable without auth anyway."""
    base_url = settings.app.WEBAPP_URL.rstrip("/")
    lines = [
        "User-agent: *",
        "Disallow: /seller",
        "Disallow: /cart",
        "Disallow: /favorites",
    ]
    if base_url:
        lines += ["", f"Sitemap: {base_url}/sitemap.xml"]
    return "\n".join(lines) + "\n"


@router.get("/sitemap.xml")
async def sitemap_xml(
    settings: FromDishka[Settings],
    product_repository: FromDishka[ProductRepository],
) -> Response:
    """Lists the storefront's publicly indexable pages: home, the catalog,
    and every published product. Deliberately excludes `/seller`, `/cart`,
    `/favorites` (see `robots_txt` above) and draft/hidden products (not in
    `list_published_for_sitemap`'s query) — a search engine has no business
    indexing either."""
    base_url = settings.app.WEBAPP_URL.rstrip("/")
    urls = [(f"{base_url}/", "daily", "1.0", None), (f"{base_url}/catalog", "daily", "0.8", None)]
    for product_id, updated_at in await product_repository.list_published_for_sitemap():
        urls.append(
            (f"{base_url}/product/{product_id}", "weekly", "0.6", updated_at.date().isoformat())
        )

    entries = []
    for loc, changefreq, priority, lastmod in urls:
        parts = [
            f"<loc>{loc}</loc>",
            f"<changefreq>{changefreq}</changefreq>",
            f"<priority>{priority}</priority>",
        ]
        if lastmod:
            parts.append(f"<lastmod>{lastmod}</lastmod>")
        entries.append(f"<url>{''.join(parts)}</url>")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(entries)
        + "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")
