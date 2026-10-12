from decimal import Decimal

from app.dto.product import ProductUpdateSchema
from app.entities.product import Availability, Product, ProductStatus
from app.repositories.product import ProductRepository
from app.shared.stock import resolve_availability


class ProductService:
    def __init__(self, product_repository: ProductRepository) -> None:
        self._product_repository = product_repository

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
