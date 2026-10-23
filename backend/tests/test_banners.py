import io
import os

from PIL import Image


def _fake_image_bytes(color: str = "red", fmt: str = "JPEG") -> bytes:
    """A real (if tiny) encoded image — save_banner_image now decodes the
    upload with Pillow to re-encode it as WebP, same as save_product_photo,
    so plain byte strings like the old `b"fake-image-bytes"` fixture no
    longer pass as a valid upload."""
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color=color).save(buffer, format=fmt)
    return buffer.getvalue()


def _fake_images() -> dict:
    return {
        "file_mobile": ("banner-mobile.jpg", _fake_image_bytes("red"), "image/jpeg"),
        "file_desktop": ("banner-desktop.jpg", _fake_image_bytes("blue"), "image/jpeg"),
    }


async def test_create_and_list_banner(client, seller):
    _, headers = seller

    response = await client.post(
        "/api/v1/seller/banners", headers=headers, files=_fake_images()
    )
    assert response.status_code == 200
    body = response.json()
    assert body["image_path_mobile"].startswith("/media/slides/")
    assert body["image_path_desktop"].startswith("/media/slides/")
    assert body["image_path_mobile"] != body["image_path_desktop"]
    # Re-encoded to WebP regardless of the uploaded files' own extension —
    # see _encode_image_to_webp in app/shared/uploads.py.
    assert body["image_path_mobile"].endswith(".webp")
    assert body["image_path_desktop"].endswith(".webp")
    assert body["link_url"] is None

    catalog_response = await client.get("/api/v1/catalog/banners")
    assert catalog_response.status_code == 200
    assert len(catalog_response.json()) == 1


async def test_banner_image_upload_is_reencoded_to_webp(client, seller):
    """The files actually written to disk are WebP-encoded, independent of
    what format/extension the seller uploaded — not just the `.webp` name
    `test_create_and_list_banner` already checks on the returned paths."""
    _, headers = seller

    response = await client.post(
        "/api/v1/seller/banners",
        headers=headers,
        files={
            "file_mobile": ("banner-mobile.png", _fake_image_bytes("red", "PNG"), "image/png"),
            "file_desktop": ("banner-desktop.png", _fake_image_bytes("blue", "PNG"), "image/png"),
        },
    )
    assert response.status_code == 200
    body = response.json()

    for key in ("image_path_mobile", "image_path_desktop"):
        disk_path = os.path.join("/tmp/vitrina-test-media", body[key].removeprefix("/media/"))
        with Image.open(disk_path) as saved:
            assert saved.format == "WEBP"


async def test_banner_image_upload_rejects_non_image_bytes(client, seller):
    """Garbage bytes with an image/* content type and a plausible filename
    must still be rejected, not silently written to disk as-is."""
    _, headers = seller

    response = await client.post(
        "/api/v1/seller/banners",
        headers=headers,
        files={
            "file_mobile": ("banner-mobile.jpg", b"not-actually-an-image", "image/jpeg"),
            "file_desktop": ("banner-desktop.jpg", _fake_image_bytes("blue"), "image/jpeg"),
        },
    )
    assert response.status_code == 400


async def test_moderator_can_manage_banners_but_not_settings(client, moderator):
    _, headers = moderator

    create_response = await client.post(
        "/api/v1/seller/banners", headers=headers, files=_fake_images()
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
            "/api/v1/seller/banners", headers=headers, files=_fake_images()
        )
        assert response.status_code == 200

    response = await client.post("/api/v1/seller/banners", headers=headers, files=_fake_images())
    assert response.status_code == 400


async def test_update_and_delete_banner(client, seller):
    _, headers = seller
    created = await client.post("/api/v1/seller/banners", headers=headers, files=_fake_images())
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
