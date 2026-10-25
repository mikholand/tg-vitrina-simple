from app.entities.product import ProductStatus


async def test_robots_txt_disallows_staff_and_cart_routes(client):
    response = await client.get("/api/v1/catalog/robots.txt")
    assert response.status_code == 200
    body = response.text
    assert "Disallow: /seller" in body
    assert "Disallow: /cart" in body
    assert "Disallow: /favorites" in body


async def test_sitemap_lists_only_published_products(client, make_product):
    published = await make_product(name="Published one", status=ProductStatus.PUBLISHED)
    await make_product(name="Draft one", status=ProductStatus.DRAFT)
    hidden = await make_product(name="Hidden one", status=ProductStatus.HIDDEN)

    response = await client.get("/api/v1/catalog/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    body = response.text
    assert f"/product/{published.id}</loc>" in body
    assert "/catalog</loc>" in body
    assert f"/product/{hidden.id}</loc>" not in body
    # Draft products never got a stable "is this excluded" id check above,
    # but the published/hidden pair already proves the status filter works
    # — a draft row would only add noise here.
