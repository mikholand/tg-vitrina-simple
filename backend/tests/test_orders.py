from app.entities.product import Availability, ProductStatus
from app.repositories.store_profile import StoreProfileRepository
from app.telegram.commands import try_configure_order_chat


async def _set_order_chat(container, chat_id: int) -> None:
    async with container() as request_container:
        store_profile_repository = await request_container.get(StoreProfileRepository)
        await store_profile_repository.set_order_notification_chat(chat_id)


async def test_checkout_creates_order_decrements_stock_and_notifies(
    client, container, customer, make_product, mock_bot_send_message
):
    _, headers = customer
    p1 = await make_product(
        name="p1",
        sku="SKU-1",
        price="100.00",
        currency="RUB",
        status=ProductStatus.PUBLISHED,
        quantity=5,
    )
    p2 = await make_product(
        name="p2", price="50.00", currency="RUB", status=ProductStatus.PUBLISHED, quantity=None
    )
    await _set_order_chat(container, -100123456789)

    response = await client.post(
        "/api/v1/catalog/orders",
        json={
            "items": [
                {"product_id": p1.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 3},
            ],
            "comment": "Позвоните перед доставкой",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == "350.00"
    assert body["notified"] is True
    assert {item["product_id"] for item in body["items"]} == {p1.id, p2.id}

    mock_bot_send_message.assert_called_once()
    _, kwargs = mock_bot_send_message.call_args
    assert kwargs["chat_id"] == -100123456789
    assert "350.00" in kwargs["text"]
    # p1's SKU shown in parens next to its name; p2 has none, so no parens.
    assert "p1 (SKU-1)" in kwargs["text"]
    assert "p2 (" not in kwargs["text"]

    # Tracked-stock product decremented; untracked (quantity=None) left alone.
    products = await client.get("/api/v1/catalog/products")
    by_id = {item["id"]: item for item in products.json()["items"]}
    assert by_id[p1.id]["quantity"] == 3
    assert by_id[p2.id]["quantity"] is None


async def test_checkout_depleting_stock_to_zero_flips_availability_to_out_of_stock(
    client, customer, make_product
):
    """A tracked "в наличии" product that a checkout sells down to exactly
    zero reads as "нет в наличии" from then on — see
    `OrderRepository.try_decrement_stock`."""
    _, headers = customer
    product = await make_product(
        price="10.00", status=ProductStatus.PUBLISHED, availability=Availability.IN_STOCK, quantity=2
    )

    response = await client.post(
        "/api/v1/catalog/orders",
        json={"items": [{"product_id": product.id, "quantity": 2}]},
        headers=headers,
    )
    assert response.status_code == 201

    products = await client.get("/api/v1/catalog/products")
    by_id = {item["id"]: item for item in products.json()["items"]}
    # `/catalog/products` only ever lists published items — sold out to
    # zero doesn't unpublish it, so it should still be there, just flagged.
    assert by_id[product.id]["quantity"] == 0
    assert by_id[product.id]["availability"] == "out_of_stock"


async def test_checkout_without_configured_chat_still_succeeds(
    client, customer, make_product, mock_bot_send_message
):
    _, headers = customer
    product = await make_product(price="10.00", status=ProductStatus.PUBLISHED, quantity=1)

    response = await client.post(
        "/api/v1/catalog/orders",
        json={"items": [{"product_id": product.id, "quantity": 1}]},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["notified"] is False
    mock_bot_send_message.assert_not_called()


async def test_checkout_rejects_insufficient_stock_without_decrementing(
    client, customer, make_product
):
    _, headers = customer
    product = await make_product(price="10.00", status=ProductStatus.PUBLISHED, quantity=1)

    response = await client.post(
        "/api/v1/catalog/orders",
        json={"items": [{"product_id": product.id, "quantity": 2}]},
        headers=headers,
    )
    assert response.status_code == 400
    assert "insufficient_stock" in response.json()["detail"]

    products = await client.get("/api/v1/catalog/products")
    by_id = {item["id"]: item for item in products.json()["items"]}
    assert by_id[product.id]["quantity"] == 1


async def test_checkout_rejects_unpublished_product(client, customer, make_product):
    _, headers = customer
    product = await make_product(price="10.00", status=ProductStatus.DRAFT, quantity=5)

    response = await client.post(
        "/api/v1/catalog/orders",
        json={"items": [{"product_id": product.id, "quantity": 1}]},
        headers=headers,
    )
    assert response.status_code == 400
    assert "product_unavailable" in response.json()["detail"]


async def test_checkout_rejects_empty_cart(client, customer):
    _, headers = customer
    response = await client.post(
        "/api/v1/catalog/orders", json={"items": []}, headers=headers
    )
    assert response.status_code == 400


async def test_checkout_without_auth_requires_contact(client, make_product):
    """No Telegram session (`OptionalUser` resolves to None) — unlike the
    old hard `CurrentUser` requirement, this no longer 401s outright, but
    `contact_name`/`contact_phone` take over as the required identity."""
    product = await make_product(price="10.00", status=ProductStatus.PUBLISHED, quantity=5)
    response = await client.post(
        "/api/v1/catalog/orders", json={"items": [{"product_id": product.id, "quantity": 1}]}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "contact_required"


async def test_checkout_without_auth_succeeds_with_contact(
    client, container, make_product, mock_bot_send_message
):
    """A guest checkout from the plain website: no Authorization header, but
    a name + phone supplied — succeeds, is attributed to no customer, and
    the Telegram notification uses the contact info in place of a Telegram
    identity."""
    product = await make_product(price="10.00", status=ProductStatus.PUBLISHED, quantity=5)
    await _set_order_chat(container, -100123456789)

    response = await client.post(
        "/api/v1/catalog/orders",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "contact_name": "Иван",
            "contact_phone": "+79990001122",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] is None
    assert body["contact_name"] == "Иван"
    assert body["contact_phone"] == "+79990001122"

    mock_bot_send_message.assert_called_once()
    _, kwargs = mock_bot_send_message.call_args
    assert "от Иван" in kwargs["text"]
    assert "+79990001122" in kwargs["text"]


async def test_seller_order_history_lists_checked_out_orders(
    client, customer, seller, make_product
):
    _, customer_headers = customer
    _, seller_headers = seller
    product = await make_product(price="20.00", status=ProductStatus.PUBLISHED, quantity=5)

    checkout = await client.post(
        "/api/v1/catalog/orders",
        json={"items": [{"product_id": product.id, "quantity": 2}]},
        headers=customer_headers,
    )
    assert checkout.status_code == 201

    response = await client.get("/api/v1/seller/orders", headers=seller_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    order = body["items"][0]
    assert order["total"] == "40.00"
    assert order["items"][0]["product_name"] == product.name
    assert order["items"][0]["quantity"] == 2


async def test_seller_order_history_requires_staff(client, customer):
    _, headers = customer
    response = await client.get("/api/v1/seller/orders", headers=headers)
    assert response.status_code == 403


async def test_set_order_chat_requires_admin_role(container, customer, seller, admin):
    customer_user, _ = customer
    seller_user, _ = seller
    admin_user, _ = admin

    assert await try_configure_order_chat(container, customer_user.id, -111) is False
    assert await try_configure_order_chat(container, seller_user.id, -111) is False
    assert await try_configure_order_chat(container, admin_user.id, -222) is True

    async with container() as request_container:
        store_profile_repository = await request_container.get(StoreProfileRepository)
        profile = await store_profile_repository.get()
    assert profile.order_notification_chat_id == -222


async def test_set_order_chat_rejects_unknown_user(container):
    assert await try_configure_order_chat(container, 999999, -333) is False
