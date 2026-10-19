from decimal import Decimal

from app.core.config import Settings
from app.dto.product import ProductCreateSchema, ProductUpdateSchema
from app.entities.product import Availability, Product, ProductStatus
from app.repositories.product import ProductRepository
from app.shared.media import media_abs_path
from app.shared.stock import resolve_availability


class ProductService:
    def __init__(self, product_repository: ProductRepository, settings: Settings) -> None:
        self._product_repository = product_repository
        self._settings = settings

    async def create_by_seller(self, payload: ProductCreateSchema) -> Product:
        """A seller-authored product starts out exactly like an
        extractor-authored draft, except it's flagged `edited_by_seller` up
        front — there's no source post for the extractor to ever match it
        against, but this keeps the invariant explicit and consistent with
        every other seller-touched product."""
        availability = resolve_availability(payload.quantity, payload.availability)
        product = await self._product_repository.create_draft(
            name=payload.name,
            price=payload.price,
            currency=payload.currency,
            description=payload.description,
            sku=payload.sku,
            availability=availability,
            quantity=payload.quantity,
            photo_paths=[],
            source_post_id=None,
        )
        product.edited_by_seller = True
        if payload.category_ids:
            await self._product_repository.set_categories(product.id, payload.category_ids)
        return product

    async def create_or_update_from_extraction(
        self,
        existing: Product | None,
        source_post_id: int | None,
        name: str,
        price: Decimal | None,
        currency: str | None,
        description: str | None,
        sku: str | None,
        availability: Availability,
        photo_paths: list[str],
    ) -> Product:
        """Called by the extractor. Never touches a product the seller has
        hand-edited — that invariant is enforced by the caller checking
        `edited_by_seller` before even calling the LLM, but we re-assert it
        here too since this is the one place writes actually happen.
        """
        if existing is not None and existing.edited_by_seller:
            return existing

        resolved_availability = resolve_availability(existing.quantity if existing else None, availability)

        if existing is None:
            return await self._product_repository.create_draft(
                name=name,
                price=price,
                currency=currency or "RUB",
                description=description,
                sku=sku,
                availability=resolved_availability,
                quantity=None,
                photo_paths=photo_paths,
                source_post_id=source_post_id,
            )

        existing.name = name
        existing.price = price
        existing.currency = currency or existing.currency
        existing.description = description
        existing.sku = sku
        existing.availability = resolved_availability
        if photo_paths:
            existing.photo_paths = photo_paths
        return existing

    async def update_by_seller(self, product: Product, payload: ProductUpdateSchema) -> Product:
        if payload.name is not None:
            product.name = payload.name
        if payload.price is not None or "price" in payload.model_fields_set:
            product.price = payload.price
        if payload.currency is not None:
            product.currency = payload.currency
        if payload.description is not None or "description" in payload.model_fields_set:
            product.description = payload.description
        if payload.sku is not None or "sku" in payload.model_fields_set:
            product.sku = payload.sku
        if payload.quantity is not None or "quantity" in payload.model_fields_set:
            product.quantity = payload.quantity
        if payload.availability is not None:
            product.availability = payload.availability
        if payload.publish_to_channel is not None:
            product.publish_to_channel = payload.publish_to_channel

        product.availability = resolve_availability(product.quantity, product.availability)
        product.edited_by_seller = True

        if payload.category_ids is not None:
            await self._product_repository.set_categories(product.id, payload.category_ids)

        return product

    async def set_status(self, product: Product, status: ProductStatus) -> Product:
        product.status = status
        return product

    async def delete_product(self, product: Product) -> None:
        """Erase a product for good, together with the media it owned.

        Irreversible by design — the seller confirms this in the dialog
        before the request is ever sent. `POST /{id}/hide` stays the
        reversible way to pull a product off the storefront.
        """
        # Read paths before delete(): the row is gone afterwards, so nothing
        # downstream could recover them from the product object anymore.
        media = [*product.photo_paths]
        if product.video_path:
            media.append(product.video_path)
        await self._product_repository.delete(product.id)
        for path in media:
            media_abs_path(self._settings, path).unlink(missing_ok=True)
