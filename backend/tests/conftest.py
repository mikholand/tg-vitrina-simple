"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database (via aiosqlite),
never against the real Postgres database. The required env vars for
`Settings` are set here, before any `app.*` module gets a chance to call
`get_settings()`, so the single cached `Settings` instance used by the whole
test session is deterministic.
"""

import os

os.environ["TELEGRAM_CHANNEL_ID"] = "123456789"
os.environ["BOT_TOKEN"] = "123456:TEST-TOKEN-FOR-UNIT-TESTS"
os.environ["JWT_SECRET"] = "test-jwt-secret-at-least-32-bytes-long-for-hs256"
os.environ["INTERNAL_API_TOKEN"] = "test-internal-token"
os.environ["SUPER_ADMIN_IDS"] = ""
os.environ["MEDIA_ROOT"] = "/tmp/vitrina-test-media"
os.environ["OPENROUTER_API_KEY"] = ""

from collections.abc import AsyncIterator, Awaitable, Callable  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from aiogram import Bot  # noqa: E402
from aiogram.types import User as TelegramUser  # noqa: E402
from dishka import Provider, Scope, make_async_container, provide  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import BigInteger  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


@compiles(BigInteger, "sqlite")
def _compile_big_integer_sqlite(element, compiler, **kw):  # noqa: ANN001, ARG001
    """SQLite's autoincrement-rowid trick only kicks in for a column that
    renders as exactly `INTEGER PRIMARY KEY`. The app's entities use
    `BigInteger` primary keys (fine on Postgres); without this override
    they'd compile to `BIGINT` on SQLite and silently fail to autoincrement.
    SQLite integers are already 64-bit, so this is a lossless, test-only
    compilation override — it does not change production (Postgres) DDL.
    """
    return "INTEGER"


from app.asgi.app import create_app  # noqa: E402
from app.clients.bot import BotClient, create_bot  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402
from app.di.providers import (  # noqa: E402
    ClientProvider,
    RepositoryProvider,
    ServiceProvider,
    SessionProvider,
)
from app.entities.base import Base  # noqa: E402
from app.entities.category import Category  # noqa: E402
from app.entities.product import Availability, Product, ProductStatus  # noqa: E402
from app.entities.raw_post import RawPost, RawPostStatus  # noqa: E402
from app.entities.user import User, UserRole  # noqa: E402
from app.shared.security import TokenPayload, create_jwt_token  # noqa: E402

# --------------------------------------------------------------------------
# Settings / DB engine
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(autouse=True)
def _mock_bot_get_me(monkeypatch: pytest.MonkeyPatch) -> None:
    """`BotClient.username()` (used when building invite/product deep links)
    calls `Bot.get_me()`, a real HTTP call to the Telegram Bot API — never
    something a unit test should do, and it would fail anyway against the
    fake `BOT_TOKEN` set above. Patched globally (autouse) rather than per
    test, since any seller-side route may end up needing a deep link."""
    fake_me = TelegramUser(id=1, is_bot=True, first_name="Test Bot", username="test_bot")
    monkeypatch.setattr(Bot, "get_me", AsyncMock(return_value=fake_me))


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    """A fresh in-memory SQLite database per test.

    `StaticPool` + `check_same_thread=False` makes every checkout share the
    same underlying connection, which is required for an in-memory SQLite DB
    to be visible across the multiple AsyncSessions the app opens per
    request.
    """
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """A single long-lived session for tests that drive services/repositories
    directly (no HTTP layer involved), e.g. extraction tests."""
    async with session_factory() as session:
        yield session


# --------------------------------------------------------------------------
# Dishka container wired against the SQLite engine, and the FastAPI app
# --------------------------------------------------------------------------


class _TestCoreProvider(Provider):
    """Mirrors `app.di.providers.CoreProvider` but serves the SQLite engine
    built for this test instead of the real Postgres one."""

    scope = Scope.APP

    def __init__(
        self,
        settings: Settings,
        engine: AsyncEngine,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._settings = settings
        self._engine = engine
        self._session_factory = session_factory
        super().__init__()

    @provide
    def provide_settings(self) -> Settings:
        return self._settings

    @provide
    def provide_engine(self) -> AsyncEngine:
        return self._engine

    @provide
    def provide_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @provide
    def provide_bot(self, settings: Settings) -> Bot:
        return create_bot(settings)

    @provide
    def provide_bot_client(self, bot: Bot) -> BotClient:
        return BotClient(bot)


@pytest_asyncio.fixture
async def container(
    settings: Settings,
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
):
    c = make_async_container(
        _TestCoreProvider(settings, engine, session_factory),
        SessionProvider(),
        RepositoryProvider(),
        ClientProvider(),
        ServiceProvider(),
    )
    yield c
    await c.close()


@pytest.fixture
def app(container):
    """Build the real FastAPI app, then swap its Dishka container for one
    wired against the SQLite test engine. Every other provider (repos,
    services, clients) is wired exactly as in production."""
    application = create_app()
    application.state.dishka_container = container
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --------------------------------------------------------------------------
# Data builders
# --------------------------------------------------------------------------


@pytest_asyncio.fixture
async def make_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[..., Awaitable[User]]:
    async def _make(
        user_id: int,
        role: UserRole = UserRole.CUSTOMER,
        tg_username: str | None = None,
        tg_photo_url: str | None = None,
    ) -> User:
        async with session_factory() as session:
            user = User(
                id=user_id, tg_username=tg_username, tg_photo_url=tg_photo_url, role=role
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    return _make


@pytest.fixture
def auth_header(settings: Settings) -> Callable[[int, UserRole], dict[str, str]]:
    def _header(user_id: int, role: UserRole) -> dict[str, str]:
        token = create_jwt_token(TokenPayload(user_id=user_id, role=role), settings)
        return {"Authorization": f"Bearer {token}"}

    return _header


@pytest_asyncio.fixture
async def customer(make_user, auth_header) -> tuple[User, dict[str, str]]:
    user = await make_user(1001, UserRole.CUSTOMER)
    return user, auth_header(user.id, user.role)


@pytest_asyncio.fixture
async def seller(make_user, auth_header) -> tuple[User, dict[str, str]]:
    user = await make_user(2001, UserRole.SELLER)
    return user, auth_header(user.id, user.role)


@pytest_asyncio.fixture
async def admin(make_user, auth_header) -> tuple[User, dict[str, str]]:
    user = await make_user(3001, UserRole.ADMIN)
    return user, auth_header(user.id, user.role)


@pytest_asyncio.fixture
async def moderator(make_user, auth_header) -> tuple[User, dict[str, str]]:
    user = await make_user(4001, UserRole.MODERATOR)
    return user, auth_header(user.id, user.role)


@pytest.fixture
def internal_header(settings: Settings) -> dict[str, str]:
    return {"X-Internal-Token": settings.security.INTERNAL_API_TOKEN.get_secret_value()}


@pytest_asyncio.fixture
async def make_category(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[..., Awaitable[Category]]:
    async def _make(
        name: str,
        code: str,
        parent_id: int | None = None,
        depth: int = 0,
        is_fallback: bool = False,
        is_hidden: bool = False,
        sort_order: int = 0,
    ) -> Category:
        async with session_factory() as session:
            category = Category(
                name=name,
                code=code,
                parent_id=parent_id,
                depth=depth,
                is_fallback=is_fallback,
                is_hidden=is_hidden,
                sort_order=sort_order,
            )
            session.add(category)
            await session.commit()
            await session.refresh(category)
            return category

    return _make


@pytest_asyncio.fixture
async def fallback_category(make_category) -> Category:
    return await make_category("Другое", "other", is_fallback=True)


@pytest_asyncio.fixture
async def make_product(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[..., Awaitable[Product]]:
    async def _make(**kwargs) -> Product:
        defaults = dict(
            name="Test product",
            currency="RUB",
            status=ProductStatus.DRAFT,
            availability=Availability.UNKNOWN,
        )
        defaults.update(kwargs)
        async with session_factory() as session:
            product = Product(**defaults)
            session.add(product)
            await session.commit()
            await session.refresh(product)
            return product

    return _make


@pytest_asyncio.fixture
async def make_raw_post(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[..., Awaitable[RawPost]]:
    async def _make(**kwargs) -> RawPost:
        defaults = dict(
            channel_id=123456789,
            message_id=1,
            posted_at=datetime.now(UTC),
            status=RawPostStatus.NEW,
        )
        defaults.update(kwargs)
        async with session_factory() as session:
            post = RawPost(**defaults)
            session.add(post)
            await session.commit()
            await session.refresh(post)
            return post

    return _make
