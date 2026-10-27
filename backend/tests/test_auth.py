import hashlib
import hmac
import time

from app.entities.user import UserRole

# Matches conftest.py's os.environ["BOT_TOKEN"] — Telegram Login Widget
# signatures are keyed by SHA256(bot_token), see
# TelegramAuthService._verify_widget_hash.
_BOT_TOKEN = "123456:TEST-TOKEN-FOR-UNIT-TESTS"


def _sign_widget_payload(payload: dict) -> dict:
    fields = {k: v for k, v in payload.items() if v is not None}
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hashlib.sha256(_BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return {**payload, "hash": computed_hash}


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


async def test_widget_login_creates_user_and_issues_token(client):
    """The plain-website login path: no WebApp init_data, just the signed
    payload Telegram's Login Widget callback hands the frontend."""
    payload = _sign_widget_payload(
        {"id": 777001, "first_name": "Анна", "username": "anna_w", "auth_date": int(time.time())}
    )

    response = await client.post("/api/v1/auth/telegram/widget", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == 777001
    assert body["role"] == UserRole.CUSTOMER.value

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert me.status_code == 200
    assert me.json()["tg_username"] == "anna_w"


async def test_widget_login_rejects_tampered_payload(client):
    """A field changed after signing no longer matches the hash — same
    HMAC-over-the-whole-payload guarantee the Mini App's init_data check
    gets from aiogram, just reconstructed by hand here since the widget's
    signature scheme is Telegram's own, not aiogram's."""
    payload = _sign_widget_payload(
        {"id": 777002, "first_name": "Борис", "auth_date": int(time.time())}
    )
    payload["first_name"] = "Виктор"

    response = await client.post("/api/v1/auth/telegram/widget", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_signature"


async def test_widget_login_rejects_stale_auth_date(client):
    payload = _sign_widget_payload(
        {"id": 777003, "first_name": "Галина", "auth_date": int(time.time()) - 25 * 3600}
    )

    response = await client.post("/api/v1/auth/telegram/widget", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "expired"


async def test_store_info_includes_bot_username_for_the_login_widget(client):
    response = await client.get("/api/v1/catalog/store")
    assert response.status_code == 200
    assert response.json()["bot_username"] == "test_bot"
