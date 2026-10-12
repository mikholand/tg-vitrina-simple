from datetime import UTC, datetime

from sqlalchemy import select

from app.entities.raw_post import RawPost


def _iso(dt: datetime | None = None) -> str:
    return (dt or datetime.now(UTC)).isoformat()


async def test_claim_job_on_fresh_pass_computes_stop_id_from_max_message_id(
    client, seller, internal_header, settings
):
    _, seller_headers = seller
    channel_id = settings.store.TELEGRAM_CHANNEL_ID

    await client.post(
        "/api/v1/internal/sync/ingest",
        json={
            "posts": [
                {"channel_id": channel_id, "message_id": 777, "posted_at": _iso()},
            ]
        },
        headers=internal_header,
    )

    await client.post("/api/v1/seller/sync/start", headers=seller_headers)

    response = await client.get("/api/v1/internal/sync/job", headers=internal_header)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["stop_id"] == 777
    assert body["cursor"] is None

    # No second job to claim until another start is requested.
    response = await client.get("/api/v1/internal/sync/job", headers=internal_header)
    assert response.json() is None


async def test_claim_job_resume_keeps_existing_cursor_and_stop_id(
    client, seller, internal_header, settings
):
    _, seller_headers = seller
    channel_id = settings.store.TELEGRAM_CHANNEL_ID

    await client.post(
        "/api/v1/internal/sync/ingest",
        json={"posts": [{"channel_id": channel_id, "message_id": 500, "posted_at": _iso()}]},
        headers=internal_header,
    )
    await client.post("/api/v1/seller/sync/start", headers=seller_headers)
    first_claim = await client.get("/api/v1/internal/sync/job", headers=internal_header)
    assert first_claim.json()["stop_id"] == 500

    await client.post(
        "/api/v1/internal/sync/progress",
        json={"done_count": 1, "cursor": 480},
        headers=internal_header,
    )
    await client.post(
        "/api/v1/internal/sync/complete",
        json={"success": False, "error": "sync_interrupted"},
        headers=internal_header,
    )

    status_after_interrupt = await client.get("/api/v1/seller/sync", headers=seller_headers)
    assert status_after_interrupt.json()["status"] == "interrupted"
    assert status_after_interrupt.json()["stop_id"] == 500
    assert status_after_interrupt.json()["cursor"] == 480

    await client.post("/api/v1/seller/sync/start", params={"resume": True}, headers=seller_headers)

    second_claim = await client.get("/api/v1/internal/sync/job", headers=internal_header)
    body = second_claim.json()
    assert body["status"] == "running"
    assert body["stop_id"] == 500  # unchanged across the resume
    assert body["cursor"] == 480  # preserved, not reset


async def test_ingest_dedups_by_media_group_and_by_lone_message_id(
    client, internal_header, settings, session_factory
):
    channel_id = settings.store.TELEGRAM_CHANNEL_ID

    response = await client.post(
        "/api/v1/internal/sync/ingest",
        json={
            "posts": [
                {
                    "channel_id": channel_id,
                    "message_id": 1,
                    "media_group_id": 10,
                    "photo_paths": ["p1.jpg"],
                    "posted_at": _iso(),
                }
            ]
        },
        headers=internal_header,
    )
    assert response.json() == {"ingested": 1}

    # Second photo of the same album arrives later as a separate message_id.
    response = await client.post(
        "/api/v1/internal/sync/ingest",
        json={
            "posts": [
                {
                    "channel_id": channel_id,
                    "message_id": 2,
                    "media_group_id": 10,
                    "photo_paths": ["p2.jpg"],
                    "posted_at": _iso(),
                }
            ]
        },
        headers=internal_header,
    )
    assert response.json() == {"ingested": 0}

    response = await client.post(
        "/api/v1/internal/sync/ingest",
        json={
            "posts": [
                {"channel_id": channel_id, "message_id": 3, "photo_paths": ["p3.jpg"], "posted_at": _iso()}
            ]
        },
        headers=internal_header,
    )
    assert response.json() == {"ingested": 1}

    # Re-ingesting the same lone message is a no-op too.
    response = await client.post(
        "/api/v1/internal/sync/ingest",
        json={
            "posts": [
                {"channel_id": channel_id, "message_id": 3, "photo_paths": ["p4.jpg"], "posted_at": _iso()}
            ]
        },
        headers=internal_header,
    )
    assert response.json() == {"ingested": 0}

    async with session_factory() as session:
        rows = (await session.execute(select(RawPost).order_by(RawPost.id))).scalars().all()

    assert len(rows) == 2  # one media-group post, one lone-message post
    album_post = next(r for r in rows if r.media_group_id == 10)
    assert album_post.photo_paths == ["p1.jpg", "p2.jpg"]
    lone_post = next(r for r in rows if r.media_group_id is None)
    assert lone_post.photo_paths == ["p3.jpg", "p4.jpg"]


async def test_progress_cursor_only_advances_toward_older_messages(
    client, seller, internal_header
):
    _, seller_headers = seller

    await client.post(
        "/api/v1/internal/sync/progress",
        json={"done_count": 1, "total_count": 10, "cursor": 1000},
        headers=internal_header,
    )
    state = (await client.get("/api/v1/seller/sync", headers=seller_headers)).json()
    assert state["cursor"] == 1000
    assert state["done_count"] == 1

    # A newer (larger) message id must NOT move the cursor backwards.
    await client.post(
        "/api/v1/internal/sync/progress",
        json={"done_count": 2, "cursor": 1500},
        headers=internal_header,
    )
    state = (await client.get("/api/v1/seller/sync", headers=seller_headers)).json()
    assert state["cursor"] == 1000
    assert state["done_count"] == 2

    # An older (smaller) message id does move it.
    await client.post(
        "/api/v1/internal/sync/progress",
        json={"done_count": 3, "cursor": 500},
        headers=internal_header,
    )
    state = (await client.get("/api/v1/seller/sync", headers=seller_headers)).json()
    assert state["cursor"] == 500
    assert state["done_count"] == 3


async def test_complete_success_resets_checkpoint(client, seller, internal_header):
    _, seller_headers = seller
    await client.post(
        "/api/v1/internal/sync/progress",
        json={"done_count": 1, "cursor": 100},
        headers=internal_header,
    )

    response = await client.post(
        "/api/v1/internal/sync/complete",
        json={"success": True},
        headers=internal_header,
    )
    assert response.status_code == 204

    state = (await client.get("/api/v1/seller/sync", headers=seller_headers)).json()
    assert state["status"] == "done"
    assert state["cursor"] is None
    assert state["stop_id"] is None
    assert state["attempts"] == 0
    assert state["last_error"] is None


async def test_complete_failure_marks_failed_and_schedules_retry(client, seller, internal_header):
    _, seller_headers = seller

    response = await client.post(
        "/api/v1/internal/sync/complete",
        json={"success": False, "error": "network_error", "retry_after_seconds": 30},
        headers=internal_header,
    )
    assert response.status_code == 204

    state = (await client.get("/api/v1/seller/sync", headers=seller_headers)).json()
    assert state["status"] == "failed"
    assert state["attempts"] == 1
    assert state["last_error"] == "network_error"
    assert state["retry_at"] is not None


async def test_internal_endpoints_require_internal_token(client):
    response = await client.get("/api/v1/internal/sync/job")
    assert response.status_code == 401

    response = await client.get(
        "/api/v1/internal/sync/job", headers={"X-Internal-Token": "wrong-token"}
    )
    assert response.status_code == 401
