import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


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
