from collections.abc import AsyncIterable

from aiogram import Bot
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.clients.bot import BotClient, create_bot
from app.clients.openrouter import OpenRouterClient
from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_session_factory
from app.repositories.banner import BannerRepository
from app.repositories.category import CategoryRepository
from app.repositories.favorite import FavoriteRepository
from app.repositories.product import ProductRepository
from app.repositories.raw_post import RawPostRepository
from app.repositories.store_profile import StoreProfileRepository
from app.repositories.sync_state import SyncStateRepository
from app.repositories.user import UserRepository
from app.repositories.view import ViewRepository
from app.services.category import CategoryService
from app.services.extraction import ExtractionService
from app.services.favorite import FavoriteService
from app.services.product import ProductService
from app.services.publishing import PublishingService
from app.services.sync import SyncOrchestrationService
from app.services.telegram_auth import TelegramAuthService
from app.services.view import ViewService


class CoreProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> Settings:
        return get_settings()

    @provide
    def engine(self, settings: Settings) -> AsyncEngine:
        return create_engine(settings)

    @provide
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @provide
    def bot(self, settings: Settings) -> Bot:
        return create_bot(settings)


class SessionProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with factory() as session, session.begin():
            yield session


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    user_repository = provide(UserRepository)
    raw_post_repository = provide(RawPostRepository)
    product_repository = provide(ProductRepository)
    category_repository = provide(CategoryRepository)
    favorite_repository = provide(FavoriteRepository)
    view_repository = provide(ViewRepository)
    sync_state_repository = provide(SyncStateRepository)
    store_profile_repository = provide(StoreProfileRepository)
    banner_repository = provide(BannerRepository)


class ClientProvider(Provider):
    scope = Scope.REQUEST

    openrouter_client = provide(OpenRouterClient)
    bot_client = provide(BotClient)


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    telegram_auth_service = provide(TelegramAuthService)
    product_service = provide(ProductService)
    category_service = provide(CategoryService)
    favorite_service = provide(FavoriteService)
    view_service = provide(ViewService)
    extraction_service = provide(ExtractionService)
    sync_service = provide(SyncOrchestrationService)
    publishing_service = provide(PublishingService)
