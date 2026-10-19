import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".webm"}

# Mirrors tg-vitrina's seller upload caps (_MAX_PHOTO_BYTES / MAX_VIDEO_BYTES) —
# the product editor's helper text promises these limits, so they need to
# actually be enforced here, not just stated in the UI.
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024


async def save_product_photo(settings: Settings, product_id: int, upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        suffix = ".jpg"

    rel_dir = f"products/{product_id}"
    abs_dir = Path(settings.app.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{suffix}"
    rel_path = f"{rel_dir}/{filename}"
    abs_path = abs_dir / filename

    content = await upload.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="photo_too_large")
    abs_path.write_bytes(content)
    return rel_path


async def save_product_video(settings: Settings, product_id: int, upload: UploadFile) -> str:
    """Same layout/convention as save_product_photo, just a different
    allowed-suffix set and fallback extension — a product has at most one
    video, but it still lives under its own products/{id}/ dir alongside the
    photos rather than overwriting a fixed filename, so a stale file from a
    previous upload never lingers mixed in with it."""
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        suffix = ".mp4"

    rel_dir = f"products/{product_id}"
    abs_dir = Path(settings.app.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{suffix}"
    rel_path = f"{rel_dir}/{filename}"
    abs_path = abs_dir / filename

    content = await upload.read()
    if len(content) > MAX_VIDEO_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="video_too_large")
    abs_path.write_bytes(content)
    return rel_path


async def save_banner_image(settings: Settings, upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        suffix = ".jpg"

    # Deliberately NOT "banners" — that path segment matches common ad-block
    # filter lists (EasyList etc. block any URL containing "/banner"), so
    # browsers with an ad blocker installed would silently fail to load the
    # storefront's own promo carousel image.
    rel_dir = "slides"
    abs_dir = Path(settings.app.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{suffix}"
    rel_path = f"{rel_dir}/{filename}"
    abs_path = abs_dir / filename

    content = await upload.read()
    abs_path.write_bytes(content)
    return rel_path


async def save_store_logo(settings: Settings, upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        suffix = ".jpg"

    rel_dir = "store"
    abs_dir = Path(settings.app.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"logo-{uuid.uuid4().hex}{suffix}"
    rel_path = f"{rel_dir}/{filename}"
    abs_path = abs_dir / filename

    content = await upload.read()
    abs_path.write_bytes(content)
    return rel_path
