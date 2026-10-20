async def test_owner_generates_link_and_customer_redeems_it(client, seller, customer):
    _, seller_headers = seller
    customer_user, customer_headers = customer

    create_response = await client.post("/api/v1/seller/invites", headers=seller_headers)
    assert create_response.status_code == 200
    invite = create_response.json()
    assert invite["url"] == f"https://t.me/test_bot/menu?startapp=invite_{invite['token']}"

    active_response = await client.get("/api/v1/seller/invites", headers=seller_headers)
    assert active_response.status_code == 200
    assert active_response.json()["token"] == invite["token"]

    redeem_response = await client.post(
        "/api/v1/invites/redeem", headers=customer_headers, json={"token": invite["token"]}
    )
    assert redeem_response.status_code == 200
    assert redeem_response.json()["id"] == customer_user.id

    # Promoted — staff endpoints are now reachable.
    products_response = await client.get("/api/v1/seller/products", headers=customer_headers)
    assert products_response.status_code == 200

    list_response = await client.get("/api/v1/seller/moderators", headers=seller_headers)
    assert [m["id"] for m in list_response.json()] == [customer_user.id]

    # Spent — no longer active, and redeeming it again fails.
    active_after = await client.get("/api/v1/seller/invites", headers=seller_headers)
    assert active_after.json() is None

    redeem_again = await client.post(
        "/api/v1/invites/redeem", headers=customer_headers, json={"token": invite["token"]}
    )
    assert redeem_again.status_code == 400
    assert redeem_again.json()["detail"] == "invite_invalid_or_expired"


async def test_creating_a_new_link_invalidates_the_old_one(client, seller, customer):
    _, seller_headers = seller
    _, customer_headers = customer

    first = (await client.post("/api/v1/seller/invites", headers=seller_headers)).json()
    second = (await client.post("/api/v1/seller/invites", headers=seller_headers)).json()
    assert first["token"] != second["token"]

    stale_redeem = await client.post(
        "/api/v1/invites/redeem", headers=customer_headers, json={"token": first["token"]}
    )
    assert stale_redeem.status_code == 400

    fresh_redeem = await client.post(
        "/api/v1/invites/redeem", headers=customer_headers, json={"token": second["token"]}
    )
    assert fresh_redeem.status_code == 200


async def test_owner_cannot_redeem_own_invite(client, seller):
    _, seller_headers = seller

    created = await client.post("/api/v1/seller/invites", headers=seller_headers)
    token = created.json()["token"]

    response = await client.post(
        "/api/v1/invites/redeem", headers=seller_headers, json={"token": token}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "user_is_owner"


async def test_redeeming_unknown_token_fails(client, customer):
    _, headers = customer
    response = await client.post(
        "/api/v1/invites/redeem", headers=headers, json={"token": "does-not-exist"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invite_invalid_or_expired"


async def test_moderator_cannot_generate_invite_link(client, moderator):
    _, headers = moderator
    response = await client.post("/api/v1/seller/invites", headers=headers)
    assert response.status_code == 403
