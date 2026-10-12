async def test_owner_can_add_and_remove_moderator(client, seller, customer):
    _, seller_headers = seller
    customer_user, _ = customer

    add_response = await client.post(
        "/api/v1/seller/moderators", headers=seller_headers, json={"user_id": customer_user.id}
    )
    assert add_response.status_code == 200
    assert add_response.json()["id"] == customer_user.id

    list_response = await client.get("/api/v1/seller/moderators", headers=seller_headers)
    assert list_response.status_code == 200
    assert [m["id"] for m in list_response.json()] == [customer_user.id]

    # Newly-promoted moderator can reach staff endpoints now.
    from app.core.config import get_settings
    from app.shared.security import TokenPayload, create_jwt_token

    settings = get_settings()
    moderator_token = create_jwt_token(
        TokenPayload(user_id=customer_user.id, role="moderator"), settings
    )
    moderator_headers = {"Authorization": f"Bearer {moderator_token}"}
    products_response = await client.get("/api/v1/seller/products", headers=moderator_headers)
    assert products_response.status_code == 200

    remove_response = await client.delete(
        f"/api/v1/seller/moderators/{customer_user.id}", headers=seller_headers
    )
    assert remove_response.status_code == 204

    products_response = await client.get("/api/v1/seller/products", headers=moderator_headers)
    assert products_response.status_code == 403


async def test_moderator_cannot_manage_moderators(client, moderator):
    _, headers = moderator
    response = await client.get("/api/v1/seller/moderators", headers=headers)
    assert response.status_code == 403


async def test_adding_unknown_user_fails(client, seller):
    _, headers = seller
    response = await client.post(
        "/api/v1/seller/moderators", headers=headers, json={"user_id": 999999}
    )
    assert response.status_code == 404


async def test_cannot_demote_owner_via_moderator_endpoint(client, seller, admin):
    _, seller_headers = seller
    admin_user, _ = admin
    response = await client.post(
        "/api/v1/seller/moderators", headers=seller_headers, json={"user_id": admin_user.id}
    )
    assert response.status_code == 400
