from app.core.start_param import encode_start_param
from app.entities.product import ProductStatus


def _fake_video() -> dict:
    return {"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")}


async def test_seller_list_products_default_and_filtered(client, seller, make_product):
    _, headers = seller
    await make_product(name="Draft one", status=ProductStatus.DRAFT)
    await make_product(name="Published one", status=ProductStatus.PUBLISHED)
    await make_product(name="Hidden one", status=ProductStatus.HIDDEN)

    response = await client.get("/api/v1/seller/products", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3

    response = await client.get(
        "/api/v1/seller/products", params={"status": "draft"}, headers=headers
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "draft"


async def test_seller_product_update_sets_edited_by_seller_and_category_ids(
    client, seller, make_product, make_category
):
    _, headers = seller
    product = await make_product(name="Original", status=ProductStatus.DRAFT)
    cat_a = await make_category("Cat A", "cat-a")
    cat_b = await make_category("Cat B", "cat-b")

    response = await client.patch(
        f"/api/v1/seller/products/{product.id}",
        json={
            "name": "Updated name",
            "price": 199.99,
            "category_ids": [cat_a.id, cat_b.id],
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated name"
    assert body["edited_by_seller"] is True
    assert sorted(body["category_ids"]) == sorted([cat_a.id, cat_b.id])

    # Round-trip: fetching again returns the same category ids.
    response = await client.get(f"/api/v1/seller/products/{product.id}", headers=headers)
    assert sorted(response.json()["category_ids"]) == sorted([cat_a.id, cat_b.id])


async def test_publish_and_hide_status_transitions(client, seller, make_product):
    _, headers = seller
    product = await make_product(status=ProductStatus.DRAFT)

    response = await client.post(f"/api/v1/seller/products/{product.id}/publish", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "published"

    response = await client.post(f"/api/v1/seller/products/{product.id}/hide", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "hidden"

    response = await client.post(f"/api/v1/seller/products/{product.id}/publish", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "published"


async def test_catalog_only_returns_published_products_with_pagination_shape(
    client, make_product
):
    await make_product(name="Draft", status=ProductStatus.DRAFT)
    await make_product(name="Hidden", status=ProductStatus.HIDDEN)
    await make_product(name="Published A", status=ProductStatus.PUBLISHED)
    await make_product(name="Published B", status=ProductStatus.PUBLISHED)
    await make_product(name="Published C", status=ProductStatus.PUBLISHED)

    response = await client.get("/api/v1/catalog/products", params={"limit": 2, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "total", "limit", "offset"}
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    assert all(item["status"] == "published" for item in body["items"])

    response = await client.get("/api/v1/catalog/products", params={"limit": 2, "offset": 2})
    body = response.json()
    assert len(body["items"]) == 1


async def test_catalog_product_detail_includes_share_url(client, make_product):
    """`share_url` powers the "Поделиться" button on the product detail
    page — the `startapp=<encoded /product/<id>>` deep-link format
    `BotClient.product_mini_app_url()` already stamps on channel-post
    buttons. Only the detail endpoint sets it (`GET /catalog/products/{id}`);
    the list endpoint leaves it null since nothing there needs a per-item bot
    round-trip."""
    product = await make_product(status=ProductStatus.PUBLISHED)

    response = await client.get(f"/api/v1/catalog/products/{product.id}")
    assert response.status_code == 200
    expected_start_param = encode_start_param(f"/product/{product.id}")
    assert (
        response.json()["share_url"]
        == f"https://t.me/test_bot/menu?startapp={expected_start_param}"
    )
    # Regression guard: an embedded webview (observed on Telegram Desktop)
    # serving a stale cached copy of this exact response from before
    # `share_url` existed on the schema is what made the "Поделиться" button
    # silently vanish for a real user — nothing upstream (FastAPI, nginx)
    # sets Cache-Control on API responses otherwise, see asgi/app.py.
    assert response.headers["cache-control"] == "no-store"

    list_response = await client.get("/api/v1/catalog/products")
    assert list_response.json()["items"][0]["share_url"] is None


async def test_seller_product_endpoints_require_seller_role(client, customer, make_product):
    _, headers = customer
    product = await make_product(status=ProductStatus.DRAFT)

    response = await client.get("/api/v1/seller/products", headers=headers)
    assert response.status_code == 403

    response = await client.post(f"/api/v1/seller/products/{product.id}/publish", headers=headers)
    assert response.status_code == 403


async def test_create_product_then_attach_photo_and_video(client, seller):
    """Mirrors the create-time upload flow the frontend now drives: create
    the row first (no id exists before this), then attach media to the id
    it comes back with — exercising both upload endpoints end to end."""
    _, headers = seller

    create_response = await client.post(
        "/api/v1/seller/products", json={"name": "Новый товар"}, headers=headers
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["photo_paths"] == []
    assert body["video_path"] is None
    product_id = body["id"]

    photo_response = await client.post(
        f"/api/v1/seller/products/{product_id}/photos",
        headers=headers,
        files={"file": ("photo.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert photo_response.status_code == 200
    photo_paths = photo_response.json()["photo_paths"]
    assert len(photo_paths) == 1
    assert photo_paths[0].startswith(f"/media/products/{product_id}/")

    video_response = await client.post(
        f"/api/v1/seller/products/{product_id}/video", headers=headers, files=_fake_video()
    )
    assert video_response.status_code == 200
    video_path = video_response.json()["video_path"]
    assert video_path.startswith(f"/media/products/{product_id}/")
    assert video_path.endswith(".mp4")

    # A second video upload replaces the first rather than stacking up.
    second_video_response = await client.post(
        f"/api/v1/seller/products/{product_id}/video", headers=headers, files=_fake_video()
    )
    assert second_video_response.status_code == 200
    assert second_video_response.json()["video_path"] != video_path
