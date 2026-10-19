from app.entities.user import UserRole


async def test_me_returns_current_user_for_valid_token(client, customer):
    user, headers = customer

    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["role"] == UserRole.CUSTOMER.value


async def test_me_returns_tg_photo_url_when_set(client, make_user, auth_header):
    user = await make_user(5001, UserRole.CUSTOMER, tg_photo_url="https://t.me/i/userpic/1.jpg")

    response = await client.get("/api/v1/auth/me", headers=auth_header(user.id, user.role))

    assert response.status_code == 200
    assert response.json()["tg_photo_url"] == "https://t.me/i/userpic/1.jpg"


async def test_me_returns_null_tg_photo_url_when_unset(client, customer):
    # Telegram only populates photo_url for Mini Apps launched from the
    # attachment menu — the common case has no photo, and the field must
    # still be present (as null) rather than omitted, since the frontend
    # relies on its presence to fall back to a letter avatar.
    _, headers = customer

    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["tg_photo_url"] is None


async def test_me_returns_seller_role(client, seller):
    user, headers = seller

    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["role"] == UserRole.SELLER.value


async def test_me_without_token_is_unauthorized(client):
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_me_with_garbage_token_is_unauthorized(client):
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"}
    )

    assert response.status_code == 401


async def test_me_with_token_for_unknown_user_is_unauthorized(client, auth_header):
    # Token is well-signed but no such user exists in the DB.
    headers = auth_header(999999, UserRole.CUSTOMER)

    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 401
