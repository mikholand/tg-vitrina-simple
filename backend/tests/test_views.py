import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.entities.product import ProductStatus
from app.entities.view import ProductView, StoreView


async def test_product_view_is_recorded_on_every_open_without_dedup(
    client, make_product, session_factory
):
    product = await make_product(status=ProductStatus.PUBLISHED)
    visitor_key = str(uuid.uuid4())
    headers = {"X-Visitor-Key": visitor_key}

    first = await client.get(f"/api/v1/catalog/products/{product.id}", headers=headers)
    assert first.status_code == 200
    assert first.json()["views_total"] == 1

    second = await client.get(f"/api/v1/catalog/products/{product.id}", headers=headers)
    assert second.status_code == 200
    assert second.json()["views_total"] == 2

    async with session_factory() as session:
        views = (
            (await session.execute(select(ProductView).where(ProductView.product_id == product.id)))
            .scalars()
            .all()
        )
    # Every open is logged, even from the same visitor on the same day.
    assert len(views) == 2


async def test_product_view_not_recorded_for_fully_anonymous_request(
    client, make_product, session_factory
):
    """No user and no visitor key -> nothing to attribute the view to."""
    product = await make_product(status=ProductStatus.PUBLISHED)

    response = await client.get(f"/api/v1/catalog/products/{product.id}")
    assert response.status_code == 200
    assert response.json()["views_total"] == 0

    async with session_factory() as session:
        views = (
            (await session.execute(select(ProductView).where(ProductView.product_id == product.id)))
            .scalars()
            .all()
        )
    assert views == []


async def test_store_view_is_deduped_per_visitor_per_day(client, session_factory):
    visitor_key = str(uuid.uuid4())
    headers = {"X-Visitor-Key": visitor_key}

    response = await client.post("/api/v1/catalog/visit", headers=headers)
    assert response.status_code == 204
    response = await client.post("/api/v1/catalog/visit", headers=headers)
    assert response.status_code == 204

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(StoreView).where(StoreView.visitor_key == uuid.UUID(visitor_key))
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert rows[0].view_date == datetime.now(UTC).date()


async def test_store_view_is_deduped_per_authenticated_user_per_day(
    client, customer, session_factory
):
    user, headers = customer

    await client.post("/api/v1/catalog/visit", headers=headers)
    await client.post("/api/v1/catalog/visit", headers=headers)
    # A visitor key is ignored once the user is authenticated for the same call.
    await client.post("/api/v1/catalog/visit", headers=headers)

    async with session_factory() as session:
        rows = (
            (await session.execute(select(StoreView).where(StoreView.user_id == user.id)))
            .scalars()
            .all()
        )
    assert len(rows) == 1


async def test_store_view_distinguishes_different_visitors(client, session_factory):
    key_a = str(uuid.uuid4())
    key_b = str(uuid.uuid4())

    await client.post("/api/v1/catalog/visit", headers={"X-Visitor-Key": key_a})
    await client.post("/api/v1/catalog/visit", headers={"X-Visitor-Key": key_b})

    async with session_factory() as session:
        rows = (await session.execute(select(StoreView))).scalars().all()
    assert len(rows) == 2
