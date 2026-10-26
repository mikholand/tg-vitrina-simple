async def test_create_and_list_contact(client, seller):
    _, headers = seller

    response = await client.post(
        "/api/v1/seller/contacts",
        headers=headers,
        json={"label": "Анна, продажи", "type": "telegram", "value": "@nova_market"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "Анна, продажи"
    assert body["type"] == "telegram"
    assert body["value"] == "@nova_market"
    assert body["is_active"] is True

    catalog_response = await client.get("/api/v1/catalog/contacts")
    assert catalog_response.status_code == 200
    contacts = catalog_response.json()
    assert len(contacts) == 1
    assert contacts[0]["url"] == "https://t.me/nova_market"


async def test_moderator_cannot_manage_contacts_or_settings(client, moderator):
    """Contacts are owner-only (CurrentSeller), same tier as shop settings and
    team management — a moderator reaches none of them, matching the
    frontend's own `requiresOwner: true` on `/seller/contacts`
    (router/index.ts). This replaced an earlier version of this test that
    asserted the opposite for contacts (a moderator could manage them over
    the API even though the Mini App's router guard never let them reach the
    page) — see `app/api/seller/contacts.py`."""
    _, headers = moderator

    create_response = await client.post(
        "/api/v1/seller/contacts",
        headers=headers,
        json={"label": "Сервис", "type": "phone", "value": "+7 999 000-00-00"},
    )
    assert create_response.status_code == 403

    settings_response = await client.get("/api/v1/seller/settings", headers=headers)
    assert settings_response.status_code == 403


async def test_contact_limit_enforced(client, seller):
    _, headers = seller

    for i in range(10):
        response = await client.post(
            "/api/v1/seller/contacts",
            headers=headers,
            json={"label": f"Менеджер {i}", "type": "telegram", "value": f"@user{i}"},
        )
        assert response.status_code == 200

    response = await client.post(
        "/api/v1/seller/contacts",
        headers=headers,
        json={"label": "Лишний", "type": "telegram", "value": "@overflow"},
    )
    assert response.status_code == 400


async def test_update_and_delete_contact(client, seller):
    _, headers = seller
    created = await client.post(
        "/api/v1/seller/contacts",
        headers=headers,
        json={"label": "Анна", "type": "telegram", "value": "@nova_market"},
    )
    contact_id = created.json()["id"]

    update_response = await client.patch(
        f"/api/v1/seller/contacts/{contact_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False

    # Inactive contacts don't reach the public catalog endpoint.
    catalog_response = await client.get("/api/v1/catalog/contacts")
    assert catalog_response.json() == []

    delete_response = await client.delete(f"/api/v1/seller/contacts/{contact_id}", headers=headers)
    assert delete_response.status_code == 204

    seller_list_response = await client.get("/api/v1/seller/contacts", headers=headers)
    assert seller_list_response.json() == []


async def test_catalog_contacts_falls_back_to_legacy_contact_tg(client, seller):
    _, headers = seller

    await client.patch(
        "/api/v1/seller/settings",
        headers=headers,
        json={"contact_tg": "@legacy_seller"},
    )

    catalog_response = await client.get("/api/v1/catalog/contacts")
    assert catalog_response.status_code == 200
    contacts = catalog_response.json()
    assert len(contacts) == 1
    assert contacts[0]["id"] == 0
    assert contacts[0]["value"] == "@legacy_seller"
    assert contacts[0]["url"] == "https://t.me/legacy_seller"


async def test_catalog_contacts_empty_when_no_contacts_and_no_legacy_fallback(client, seller):
    # `seller` fixture starts with a fresh store profile — `contact_tg`
    # defaults to None (STORE_CONTACT_TG is unset in test config), and
    # `StoreProfileRepository.update()` treats an explicit None as "leave
    # unchanged" rather than "clear", so there's no API call needed here.
    catalog_response = await client.get("/api/v1/catalog/contacts")
    assert catalog_response.status_code == 200
    assert catalog_response.json() == []
