import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".webm"}

# Mirrors tg-vitrina's seller upload caps (_MAX_PHOTO_BYTES / MAX_VIDEO_BYTES) —
# the product editor's helper text promises these limits, so they need to
# actually be enforced here, not just stated in the UI.
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024

# Every product photo is re-encoded to WebP at this quality on upload (see
# `_encode_product_photo` below), regardless of what format the seller's
# phone/camera produced — smaller files on disk/over the wire, and one
# consistent format the frontend never has to branch on.
PRODUCT_PHOTO_WEBP_QUALITY = 80


def _encode_product_photo(content: bytes) -> bytes:
    """Decodes arbitrary uploaded image bytes and re-encodes them as WebP.
    Raises HTTPException(400) for anything Pillow can't parse as an image —
    the suffix-based check this replaced only validated the *filename*, not
    the actual bytes, so a non-image upload used to be written to disk as-is
    and only fail later, whenever something tried to actually load it as a
    photo."""
    try:
        image = Image.open(io.BytesIO(content))
        # Forces the actual pixel decode now (Image.open() is lazy) so a
        # truncated/corrupt file raises here, not on first use later.
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_image") from exc

    # Bakes the EXIF orientation tag into the pixels before the re-encode
    # below strips EXIF entirely — otherwise a photo shot in portrait on a
    # phone would end up sideways once that metadata is gone.
    image = ImageOps.exif_transpose(image) or image

    # WebP handles alpha directly; only palette mode ("P", e.g. GIF) needs
    # an explicit conversion first, or Pillow raises on save().
    if image.mode == "P":
        image = image.convert("RGBA" if "transparency" in image.info else "RGB")

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=PRODUCT_PHOTO_WEBP_QUALITY)
    return buffer.getvalue()


async def save_product_photo(settings: Settings, product_id: int, upload: UploadFile) -> str:
    rel_dir = f"products/{product_id}"
    abs_dir = Path(settings.app.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    content = await upload.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="photo_too_large")
    webp_content = _encode_product_photo(content)

    # Always .webp now — the re-encode above makes the original suffix
    # meaningless, and a mismatched extension (e.g. "photo.jpg" containing
    # WebP bytes) would confuse anything that sniffs the file by name later.
    filename = f"{uuid.uuid4().hex}.webp"
    rel_path = f"{rel_dir}/{filename}"
    abs_path = abs_dir / filename
    abs_path.write_bytes(webp_content)
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
