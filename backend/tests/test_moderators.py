async def test_owner_can_list_and_remove_moderator(client, seller, moderator):
    _, seller_headers = seller
    moderator_user, moderator_headers = moderator

    list_response = await client.get("/api/v1/seller/moderators", headers=seller_headers)
    assert list_response.status_code == 200
    assert [m["id"] for m in list_response.json()] == [moderator_user.id]

    # A moderator can reach staff endpoints.
    products_response = await client.get("/api/v1/seller/products", headers=moderator_headers)
    assert products_response.status_code == 200

    remove_response = await client.delete(
        f"/api/v1/seller/moderators/{moderator_user.id}", headers=seller_headers
    )
    assert remove_response.status_code == 204

    products_response = await client.get("/api/v1/seller/products", headers=moderator_headers)
    assert products_response.status_code == 403


async def test_moderator_cannot_manage_moderators(client, moderator):
    _, headers = moderator
    response = await client.get("/api/v1/seller/moderators", headers=headers)
    assert response.status_code == 403


async def test_removing_unknown_moderator_fails(client, seller):
    _, headers = seller
    response = await client.delete("/api/v1/seller/moderators/999999", headers=headers)
    assert response.status_code == 404
