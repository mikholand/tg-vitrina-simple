from app.entities.product import ProductStatus


async def test_add_list_remove_favorite(client, customer, make_product):
    _, headers = customer
    product = await make_product(status=ProductStatus.PUBLISHED)

    response = await client.put(f"/api/v1/favorites/{product.id}", headers=headers)
    assert response.status_code == 204

    response = await client.get("/api/v1/favorites", headers=headers)
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert ids == [product.id]

    response = await client.delete(f"/api/v1/favorites/{product.id}", headers=headers)
    assert response.status_code == 204

    response = await client.get("/api/v1/favorites", headers=headers)
    assert response.json() == []


async def test_add_favorite_is_idempotent(client, customer, make_product):
    _, headers = customer
    product = await make_product(status=ProductStatus.PUBLISHED)

    await client.put(f"/api/v1/favorites/{product.id}", headers=headers)
    response = await client.put(f"/api/v1/favorites/{product.id}", headers=headers)
    assert response.status_code == 204

    response = await client.get("/api/v1/favorites", headers=headers)
    assert [p["id"] for p in response.json()] == [product.id]


async def test_merge_favorites_absorbs_anonymous_ids_without_duplicating(
    client, customer, make_product
):
    _, headers = customer
    p1 = await make_product(name="p1", status=ProductStatus.PUBLISHED)
    p2 = await make_product(name="p2", status=ProductStatus.PUBLISHED)
    p3 = await make_product(name="p3", status=ProductStatus.PUBLISHED)

    # User already has p1 favorited server-side.
    await client.put(f"/api/v1/favorites/{p1.id}", headers=headers)

    # Client sends its anonymous localStorage list, which also contains p1.
    response = await client.post(
        "/api/v1/favorites/merge",
        json={"product_ids": [p1.id, p2.id, p3.id]},
        headers=headers,
    )
    assert response.status_code == 204

    response = await client.get("/api/v1/favorites", headers=headers)
    ids = sorted(p["id"] for p in response.json())
    assert ids == sorted([p1.id, p2.id, p3.id])
    # No duplicates: exactly 3 entries, not 4.
    assert len(response.json()) == 3


async def test_favorites_require_auth(client, make_product):
    product = await make_product(status=ProductStatus.PUBLISHED)

    response = await client.put(f"/api/v1/favorites/{product.id}")
    assert response.status_code == 401

    response = await client.get("/api/v1/favorites")
    assert response.status_code == 401
