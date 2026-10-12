def _fake_image() -> dict:
    return {"file": ("banner.jpg", b"fake-image-bytes", "image/jpeg")}


async def test_create_and_list_banner(client, seller):
    _, headers = seller

    response = await client.post(
        "/api/v1/seller/banners", headers=headers, files=_fake_image()
    )
    assert response.status_code == 200
    body = response.json()
    assert body["image_path"].startswith("/media/banners/")
    assert body["link_url"] is None

    catalog_response = await client.get("/api/v1/catalog/banners")
    assert catalog_response.status_code == 200
    assert len(catalog_response.json()) == 1


async def test_moderator_can_manage_banners_but_not_settings(client, moderator):
    _, headers = moderator

    create_response = await client.post(
        "/api/v1/seller/banners", headers=headers, files=_fake_image()
    )
    assert create_response.status_code == 200

    settings_response = await client.get("/api/v1/seller/settings", headers=headers)
    assert settings_response.status_code == 403

    moderators_response = await client.get("/api/v1/seller/moderators", headers=headers)
    assert moderators_response.status_code == 403


async def test_banner_limit_enforced(client, seller):
    _, headers = seller

    for _ in range(3):
        response = await client.post(
            "/api/v1/seller/banners", headers=headers, files=_fake_image()
        )
        assert response.status_code == 200

    response = await client.post("/api/v1/seller/banners", headers=headers, files=_fake_image())
    assert response.status_code == 400


async def test_update_and_delete_banner(client, seller):
    _, headers = seller
    created = await client.post("/api/v1/seller/banners", headers=headers, files=_fake_image())
    banner_id = created.json()["id"]

    update_response = await client.patch(
        f"/api/v1/seller/banners/{banner_id}",
        headers=headers,
        json={"link_url": "https://example.com"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["link_url"] == "https://example.com"

    # Explicit null clears it (model_fields_set semantics).
    clear_response = await client.patch(
        f"/api/v1/seller/banners/{banner_id}",
        headers=headers,
        json={"link_url": None},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["link_url"] is None

    delete_response = await client.delete(f"/api/v1/seller/banners/{banner_id}", headers=headers)
    assert delete_response.status_code == 204

    catalog_response = await client.get("/api/v1/catalog/banners")
    assert catalog_response.json() == []
