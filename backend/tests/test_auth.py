import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.entities.user import UserRole
from app.services import telegram_auth

# Matches conftest.py's os.environ["BOT_TOKEN"] = "123456:TEST-TOKEN-FOR-UNIT-TESTS"
# — an OIDC id_token's `aud` claim is the bot's numeric id, the part of
# BOT_TOKEN before the colon (see Settings.telegram.bot_id).
_BOT_ID = "123456"

# Generated once per test run, not per test — a 2048-bit RSA keypair takes
# tens of milliseconds to generate, and nothing here needs a fresh one each
# time.
_TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _FakeSigningKey:
    def __init__(self, key) -> None:
        self.key = key


class _FakeJwksClient:
    """Stands in for `PyJWKClient` in tests — no real network call to
    Telegram's JWKS endpoint, just hands back the matching test public key
    regardless of the token's `kid`."""

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(_TEST_PRIVATE_KEY.public_key())


@pytest.fixture(autouse=True)
def _fake_telegram_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test in this module goes through `TelegramAuthService.
    login_via_widget` with a token signed by `_TEST_PRIVATE_KEY` instead of
    Telegram's real one — this swaps in the matching fake JWKS client so
    `_verify_widget_id_token` validates against it rather than hitting
    `oauth.telegram.org` for real."""
    monkeypatch.setattr(telegram_auth, "_get_jwks_client", lambda: _FakeJwksClient())


def _sign_id_token(claims: dict) -> str:
    return jwt.encode(claims, _TEST_PRIVATE_KEY, algorithm="RS256")


def _valid_claims(**overrides) -> dict:
    now = int(time.time())
    claims = {
        "iss": telegram_auth.TELEGRAM_OIDC_ISSUER,
        "aud": _BOT_ID,
        # Deliberately NOT the Telegram user id (see
        # test_widget_login_uses_id_claim_not_sub_for_the_user_id below) —
        # a long, unrelated opaque OIDC subject identifier, same shape
        # Telegram's own example token uses.
        "sub": "1234123412341234123",
        "iat": now,
        "exp": now + 3600,
        "id": 777001,
        "name": "Анна Иванова",
        "given_name": "Анна",
        "family_name": "Иванова",
        "preferred_username": "anna_w",
        "picture": "https://cdn.telesco.pe/file/anna.jpg",
    }
    claims.update(overrides)
    return claims


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
    OIDC id_token Telegram's Login Widget hands the frontend (see
    https://core.telegram.org/bots/telegram-login — the legacy HMAC-signed
    widget this replaced no longer accepts a bot registered through
    @BotFather's current Login Widget panel)."""
    id_token = _sign_id_token(_valid_claims())

    response = await client.post("/api/v1/auth/telegram/widget", json={"id_token": id_token})
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == 777001
    assert body["role"] == UserRole.CUSTOMER.value

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["tg_username"] == "anna_w"
    assert me.json()["tg_first_name"] == "Анна"
    assert me.json()["tg_last_name"] == "Иванова"


async def test_widget_login_uses_id_claim_not_sub_for_the_user_id(client):
    """`sub` is an opaque OIDC subject id, not Telegram's user id — using it
    would create a user record disconnected from the one the Mini App's
    init_data login creates for the same person (see
    TelegramAuthService.login_via_widget's docstring)."""
    id_token = _sign_id_token(_valid_claims(id=777002, sub="9999999999999999999"))

    response = await client.post("/api/v1/auth/telegram/widget", json={"id_token": id_token})
    assert response.status_code == 200
    assert response.json()["user_id"] == 777002


async def test_widget_login_rejects_tampered_token(client):
    id_token = _sign_id_token(_valid_claims())
    tampered = id_token[:-4] + ("0000" if not id_token.endswith("0000") else "1111")

    response = await client.post("/api/v1/auth/telegram/widget", json={"id_token": tampered})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_signature"


async def test_widget_login_rejects_expired_token(client):
    now = int(time.time())
    id_token = _sign_id_token(_valid_claims(iat=now - 7200, exp=now - 3600))

    response = await client.post("/api/v1/auth/telegram/widget", json={"id_token": id_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_signature"


async def test_widget_login_rejects_wrong_audience(client):
    """A token whose `aud` doesn't match this bot's id must not be accepted
    — otherwise a Telegram Login token for an unrelated bot could log a
    visitor into this site."""
    id_token = _sign_id_token(_valid_claims(aud="999999"))

    response = await client.post("/api/v1/auth/telegram/widget", json={"id_token": id_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_signature"


async def test_widget_login_rejects_wrong_issuer(client):
    id_token = _sign_id_token(_valid_claims(iss="https://evil.example.com"))

    response = await client.post("/api/v1/auth/telegram/widget", json={"id_token": id_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_signature"


async def test_store_info_includes_bot_client_id_for_the_login_widget(client):
    response = await client.get("/api/v1/catalog/store")
    assert response.status_code == 200
    assert response.json()["bot_client_id"] == 123456
