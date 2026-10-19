import json

import pytest

from app.entities.raw_post import RawPostStatus
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.raw_post import RawPostRepository
from app.services.category import CategoryService
from app.services.extraction import ExtractionService
from app.services.product import ProductService


class FakeOpenRouterClient:
    """Stands in for `app.clients.openrouter.OpenRouterClient`. Returns
    canned JSON payloads instead of calling a real LLM."""

    def __init__(self, payloads: list[dict]) -> None:
        self._payloads = payloads
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    async def complete_json(self, system_prompt: str, user_prompt: str):
        from app.dto.extraction import ExtractionResult

        self.calls += 1
        payload = self._payloads[min(self.calls - 1, len(self._payloads) - 1)]
        return ExtractionResult(content=json.dumps(payload), model="fake-model")


def _build_service(db_session, settings, fake_client) -> ExtractionService:
    raw_post_repository = RawPostRepository(db_session)
    product_repository = ProductRepository(db_session)
    category_repository = CategoryRepository(db_session)
    category_service = CategoryService(category_repository)
    product_service = ProductService(product_repository, settings)
    return ExtractionService(
        settings=settings,
        raw_post_repository=raw_post_repository,
        product_repository=product_repository,
        product_service=product_service,
        category_service=category_service,
        openrouter_client=fake_client,
    )


@pytest.fixture
async def clothing_category(make_category, fallback_category):
    # depth-0 category so its path label is just its own name.
    return await make_category("Одежда", "odezhda")


async def test_process_pending_creates_product_draft_from_raw_post(
    db_session, settings, make_raw_post, clothing_category, fallback_category
):
    raw_post = await make_raw_post(raw_text="Куртка зимняя, тёплая", status=RawPostStatus.NEW)
    fake_client = FakeOpenRouterClient(
        [
            {
                "name": "Куртка зимняя",
                "price": 5000,
                "currency": "RUB",
                "description": "Тёплая зимняя куртка",
                "sku": "JCK-1",
                "availability": "in_stock",
                "category": "Одежда",
            }
        ]
    )
    service = _build_service(db_session, settings, fake_client)

    result = await service.process_pending()

    assert result == {"claimed": 1, "extracted": 1, "failed": 0, "skipped": 0}
    assert fake_client.calls == 1

    raw_post_repository = RawPostRepository(db_session)
    product_repository = ProductRepository(db_session)

    refreshed_post = await raw_post_repository.get(raw_post.id)
    assert refreshed_post.status == RawPostStatus.EXTRACTED
    assert refreshed_post.product_id is not None

    product = await product_repository.get(refreshed_post.product_id)
    assert product.name == "Куртка зимняя"
    assert product.source_post_id == raw_post.id
    assert product.edited_by_seller is False
    category_ids = await product_repository.get_category_ids(product.id)
    assert category_ids == [clothing_category.id]


async def test_process_pending_skips_raw_post_with_no_name(
    db_session, settings, make_raw_post, fallback_category
):
    raw_post = await make_raw_post(raw_text="???", status=RawPostStatus.NEW)
    fake_client = FakeOpenRouterClient([{"name": None}])
    service = _build_service(db_session, settings, fake_client)

    result = await service.process_pending()

    assert result == {"claimed": 1, "extracted": 0, "failed": 1, "skipped": 0}
    raw_post_repository = RawPostRepository(db_session)
    refreshed = await raw_post_repository.get(raw_post.id)
    assert refreshed.status == RawPostStatus.FAILED


async def test_extraction_never_overwrites_a_product_edited_by_seller(
    db_session, settings, make_raw_post, make_product, fallback_category
):
    raw_post = await make_raw_post(raw_text="Новое описание из поста", status=RawPostStatus.NEW)
    product = await make_product(
        name="Seller-chosen name",
        description="Seller-chosen description",
        edited_by_seller=True,
        source_post_id=raw_post.id,
    )

    # If the guard didn't short-circuit, this would be called and the
    # assertion failure inside would blow up the test.
    fake_client = FakeOpenRouterClient(
        [{"name": "LLM would overwrite this", "category": None}]
    )
    service = _build_service(db_session, settings, fake_client)

    result = await service.process_pending()

    assert result == {"claimed": 1, "extracted": 1, "failed": 0, "skipped": 0}
    assert fake_client.calls == 0  # LLM must never be called for an edited product.

    product_repository = ProductRepository(db_session)
    refreshed_product = await product_repository.get(product.id)
    assert refreshed_product.name == "Seller-chosen name"
    assert refreshed_product.description == "Seller-chosen description"

    raw_post_repository = RawPostRepository(db_session)
    refreshed_post = await raw_post_repository.get(raw_post.id)
    assert refreshed_post.status == RawPostStatus.EXTRACTED
    assert refreshed_post.product_id == product.id


async def test_rerunning_extraction_still_does_not_overwrite_edited_product(
    db_session, settings, make_raw_post, make_product, fallback_category
):
    """Even if a RawPost is forced back to NEW (e.g. a bug elsewhere re-queues
    it), the iron rule holds: a seller-edited product is never touched."""
    raw_post = await make_raw_post(raw_text="post text", status=RawPostStatus.NEW)
    product = await make_product(
        name="Seller-chosen name",
        edited_by_seller=True,
        source_post_id=raw_post.id,
    )
    fake_client = FakeOpenRouterClient([{"name": "should never be used"}])
    service = _build_service(db_session, settings, fake_client)

    await service.process_pending()

    # Force the raw post back to NEW to simulate a second pass over it.
    raw_post_repository = RawPostRepository(db_session)
    refreshed_post = await raw_post_repository.get(raw_post.id)
    refreshed_post.status = RawPostStatus.NEW
    await db_session.flush()

    result = await service.process_pending()

    assert result["extracted"] == 1
    assert fake_client.calls == 0

    product_repository = ProductRepository(db_session)
    refreshed_product = await product_repository.get(product.id)
    assert refreshed_product.name == "Seller-chosen name"


async def test_process_pending_noop_when_llm_not_configured(
    db_session, settings, make_raw_post
):
    await make_raw_post(status=RawPostStatus.NEW)

    class UnconfiguredClient(FakeOpenRouterClient):
        def is_configured(self) -> bool:
            return False

    service = _build_service(db_session, settings, UnconfiguredClient([]))

    result = await service.process_pending()

    assert result == {"claimed": 0, "extracted": 0, "failed": 0, "skipped": 0}
