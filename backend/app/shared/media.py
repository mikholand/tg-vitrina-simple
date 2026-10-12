from pathlib import Path

from app.core.config import Settings


def media_abs_path(settings: Settings, relative_path: str) -> Path:
    return Path(settings.app.MEDIA_ROOT) / relative_path


def media_url(relative_path: str) -> str:
    """Host-relative URL — no S3, media is served by the backend/nginx."""
    return f"/media/{relative_path.lstrip('/')}"
