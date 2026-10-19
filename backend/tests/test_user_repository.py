from app.entities.user import UserRole
from app.repositories.user import UserRepository


async def test_upsert_from_telegram_creates_user_with_photo_url(db_session):
    repo = UserRepository(db_session)

    user = await repo.upsert_from_telegram(
        user_id=7001,
        tg_username="alice",
        tg_first_name="Alice",
        tg_last_name=None,
        tg_photo_url="https://t.me/i/userpic/1.jpg",
    )

    assert user.tg_photo_url == "https://t.me/i/userpic/1.jpg"


async def test_upsert_from_telegram_refreshes_photo_url_on_repeat_login(db_session):
    # Telegram photo URLs can rotate/expire, so every login (not just the
    # first) must overwrite the stored value — including clearing it back to
    # null if the latest init_data no longer carries one.
    repo = UserRepository(db_session)
    await repo.upsert_from_telegram(
        user_id=7002,
        tg_username="bob",
        tg_first_name="Bob",
        tg_last_name=None,
        tg_photo_url="https://t.me/i/userpic/old.jpg",
    )

    updated = await repo.upsert_from_telegram(
        user_id=7002,
        tg_username="bob",
        tg_first_name="Bob",
        tg_last_name=None,
        tg_photo_url="https://t.me/i/userpic/new.jpg",
    )
    assert updated.tg_photo_url == "https://t.me/i/userpic/new.jpg"

    cleared = await repo.upsert_from_telegram(
        user_id=7002,
        tg_username="bob",
        tg_first_name="Bob",
        tg_last_name=None,
        tg_photo_url=None,
    )
    assert cleared.tg_photo_url is None


async def test_upsert_from_telegram_defaults_photo_url_to_none(db_session):
    repo = UserRepository(db_session)

    user = await repo.upsert_from_telegram(
        user_id=7003, tg_username="carol", tg_first_name="Carol", tg_last_name=None
    )

    assert user.tg_photo_url is None
    assert user.role == UserRole.CUSTOMER
