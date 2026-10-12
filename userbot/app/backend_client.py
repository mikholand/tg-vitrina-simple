from datetime import datetime
from typing import Any

import httpx

from app.config import Settings


class SyncJob:
    def __init__(self, data: dict[str, Any]) -> None:
        self.status: str = data["status"]
        self.cursor: int | None = data["cursor"]
        self.stop_id: int | None = data["stop_id"]
        self.done_count: int = data["done_count"]
        self.total_count: int | None = data["total_count"]


class RawPostPayload:
    def __init__(
        self,
        channel_id: int,
        message_id: int,
        media_group_id: int | None,
        raw_text: str | None,
        photo_paths: list[str],
        posted_at: datetime,
    ) -> None:
        self.channel_id = channel_id
        self.message_id = message_id
        self.media_group_id = media_group_id
        self.raw_text = raw_text
        self.photo_paths = photo_paths
        self.posted_at = posted_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "media_group_id": self.media_group_id,
            "raw_text": self.raw_text,
            "photo_paths": self.photo_paths,
            "posted_at": self.posted_at.isoformat(),
        }


class BackendClient:
    """Talks to the backend's internal sync API — the only channel through
    which this separate userbot process touches the storefront's data.
    """

    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.BACKEND_INTERNAL_URL,
            headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_channel_id(self) -> int:
        response = await self._client.get("/channel")
        response.raise_for_status()
        return response.json()["channel_id"]

    async def claim_job(self) -> SyncJob | None:
        response = await self._client.get("/job")
        response.raise_for_status()
        data = response.json()
        return SyncJob(data) if data else None

    async def is_stop_requested(self) -> bool:
        response = await self._client.get("/stop-requested")
        response.raise_for_status()
        return response.json()["stop_requested"]

    async def ingest_batch(self, posts: list[RawPostPayload]) -> int:
        response = await self._client.post(
            "/ingest", json={"posts": [p.to_dict() for p in posts]}
        )
        response.raise_for_status()
        return response.json()["ingested"]

    async def update_progress(
        self, done_count: int, total_count: int | None, cursor: int | None
    ) -> None:
        response = await self._client.post(
            "/progress",
            json={"done_count": done_count, "total_count": total_count, "cursor": cursor},
        )
        response.raise_for_status()

    async def complete(
        self, success: bool, error: str | None, retry_after_seconds: int | None = None
    ) -> None:
        response = await self._client.post(
            "/complete",
            json={
                "success": success,
                "error": error,
                "retry_after_seconds": retry_after_seconds,
            },
        )
        response.raise_for_status()
