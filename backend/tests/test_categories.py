async def test_catalog_excludes_hidden_categories(client, make_category):
    await make_category("Visible", "visible")
    await make_category("Hidden", "hidden", is_hidden=True)

    response = await client.get("/api/v1/catalog/categories")

    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Visible" in names
    assert "Hidden" not in names


async def test_seller_catalog_includes_hidden_categories(client, seller, make_category):
    _, headers = seller
    await make_category("Visible", "visible")
    await make_category("Hidden", "hidden", is_hidden=True)

    response = await client.get("/api/v1/seller/categories", headers=headers)

    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Visible" in names
    assert "Hidden" in names


async def test_seller_category_listing_requires_seller_role(client, customer, make_category):
    _, headers = customer
    await make_category("Visible", "visible")

    response = await client.get("/api/v1/seller/categories", headers=headers)

    assert response.status_code == 403


async def test_visibility_toggle_persists(client, seller, make_category):
    _, headers = seller
    category = await make_category("Toggle me", "toggle-me")

    response = await client.patch(
        f"/api/v1/seller/categories/{category.id}/visibility",
        json={"is_hidden": True},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["is_hidden"] is True

    # Persisted: shows up as hidden for the seller, and disappears from catalog.
    seller_list = await client.get("/api/v1/seller/categories", headers=headers)
    updated = next(c for c in seller_list.json() if c["id"] == category.id)
    assert updated["is_hidden"] is True

    catalog_list = await client.get("/api/v1/catalog/categories")
    assert category.id not in [c["id"] for c in catalog_list.json()]

    # Toggle back off.
    response = await client.patch(
        f"/api/v1/seller/categories/{category.id}/visibility",
        json={"is_hidden": False},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["is_hidden"] is False

    catalog_list = await client.get("/api/v1/catalog/categories")
    assert category.id in [c["id"] for c in catalog_list.json()]
