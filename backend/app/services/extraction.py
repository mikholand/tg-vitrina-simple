import asyncio
import json
import time
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError

from pydantic import ValidationError

from app.clients.openrouter import OpenRouterClient
from app.core.config import Settings
from app.core.logging import get_logger
from app.dto.extraction import ProductExtractionSchema
from app.entities.raw_post import RawPost
from app.repositories.product import ProductRepository
from app.repositories.raw_post import RawPostRepository
from app.services.category import CategoryService
from app.services.product import ProductService
from app.services.prompts import EXTRACTION_SYSTEM_TEMPLATE, EXTRACTION_USER_TEMPLATE

logger = get_logger(__name__)


def _parse_json_payload(content: str) -> dict | None:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        stripped = text.lstrip()
        if stripped.lower().startswith("json"):
            text = stripped[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


class ExtractionService:
    def __init__(
        self,
        settings: Settings,
        raw_post_repository: RawPostRepository,
        product_repository: ProductRepository,
        product_service: ProductService,
        category_service: CategoryService,
        openrouter_client: OpenRouterClient,
    ) -> None:
        self._settings = settings
        self._raw_post_repository = raw_post_repository
        self._product_repository = product_repository
        self._product_service = product_service
        self._category_service = category_service
        self._openrouter_client = openrouter_client

    async def process_pending(self) -> dict[str, int]:
        if not self._openrouter_client.is_configured():
            return {"claimed": 0, "extracted": 0, "failed": 0, "skipped": 0}

        posts = await self._raw_post_repository.claim_new_batch(self._settings.extractor.EXTRACTOR_BATCH_SIZE)
        if not posts:
            return {"claimed": 0, "extracted": 0, "failed": 0, "skipped": 0}

        semaphore = asyncio.Semaphore(self._settings.extractor.EXTRACTOR_CONCURRENCY)

        async def guarded(post: RawPost) -> bool:
            async with semaphore:
                try:
                    return await self._extract_one(post)
                except Exception:
                    logger.exception("extraction_unhandled_error", raw_post_id=post.id)
                    await self._raw_post_repository.mark_failed(post.id)
                    return False

        outcomes = await asyncio.gather(*(guarded(p) for p in posts))
        extracted = sum(1 for ok in outcomes if ok)
        failed = len(outcomes) - extracted
        return {"claimed": len(posts), "extracted": extracted, "failed": failed, "skipped": 0}

    async def _extract_one(self, raw_post: RawPost) -> bool:
        existing = await self._product_repository.get_by_source_post(raw_post.id)

        # The iron rule: a seller-edited product is never touched again.
        if existing is not None and existing.edited_by_seller:
            await self._raw_post_repository.mark_extracted(raw_post.id, existing.id)
            return True

        schema = await self._call_with_retries(raw_post)
        if schema is None or not schema.name:
            await self._raw_post_repository.mark_failed(raw_post.id)
            return False

        price = self._safe_decimal(schema.price)
        category = await self._category_service.resolve_label(schema.category)

        product = await self._product_service.create_or_update_from_extraction(
            existing=existing,
            source_post_id=raw_post.id,
            name=schema.name,
            price=price,
            currency=schema.currency,
            description=schema.description,
            sku=schema.sku,
            availability=schema.availability,
            photo_paths=raw_post.photo_paths,
        )
        await self._product_repository.set_categories(product.id, [category.id])
        await self._raw_post_repository.mark_extracted(raw_post.id, product.id)
        return True

    @staticmethod
    def _safe_decimal(value: float | None) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    async def _call_with_retries(self, raw_post: RawPost) -> ProductExtractionSchema | None:
        catalog_labels = list((await self._category_service.list_selectable_paths()).keys())
        catalog_text = "\n".join(f"- {label}" for label in [*catalog_labels, "Другое"])
        system_prompt = EXTRACTION_SYSTEM_TEMPLATE.format(catalog=catalog_text)
        user_prompt = EXTRACTION_USER_TEMPLATE.format(raw_text=raw_post.raw_text or "")

        max_attempts = self._settings.extractor.EXTRACTOR_MAX_RETRIES + 1
        for attempt in range(1, max_attempts + 1):
            started = time.monotonic()
            try:
                result = await self._openrouter_client.complete_json(system_prompt, user_prompt)
            except Exception as exc:
                logger.warning(
                    "extraction_call_error", raw_post_id=raw_post.id, attempt=attempt, error=str(exc)
                )
                continue

            latency_ms = int((time.monotonic() - started) * 1000)
            payload = _parse_json_payload(result.content)
            schema: ProductExtractionSchema | None = None
            if payload is not None:
                try:
                    schema = ProductExtractionSchema.model_validate(payload)
                except ValidationError:
                    schema = None

            logger.info(
                "extraction_call",
                raw_post_id=raw_post.id,
                message_id=raw_post.message_id,
                model=result.model,
                attempt=attempt,
                latency_ms=latency_ms,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
                outcome="parsed" if schema is not None else "invalid_json",
            )

            if schema is not None:
                return schema

        return None
