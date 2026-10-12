from app.entities.product import ProductStatus


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


async def test_seller_product_endpoints_require_seller_role(client, customer, make_product):
    _, headers = customer
    product = await make_product(status=ProductStatus.DRAFT)

    response = await client.get("/api/v1/seller/products", headers=headers)
    assert response.status_code == 403

    response = await client.post(f"/api/v1/seller/products/{product.id}/publish", headers=headers)
    assert response.status_code == 403
