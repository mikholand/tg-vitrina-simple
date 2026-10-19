import mimetypes
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, catalog, favorites, health, internal_sync
from app.api import invites as invite_redeem
from app.api.seller import (
    banners,
    categories,
    contacts,
    moderators,
    products,
    raw_posts,
    stats,
    sync,
)
from app.api.seller import (
    invites as seller_invites,
)
from app.api.seller import settings as seller_settings
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.di.container import build_container

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app.LOG_LEVEL)

    app = FastAPI(title="tg-vitrina", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Starlette's StaticFiles relies on Python's mimetypes module to derive
    # Content-Type from the file extension, and that module's table doesn't
    # include image/webp on every platform/Python build (confirmed missing
    # in prod's container even on 3.12) — it falls back to
    # application/octet-stream, which makes browsers download uploaded .webp
    # banners/photos instead of displaying them inline. Registered explicitly
    # so it's correct regardless of the underlying OS's mime.types file.
    mimetypes.add_type("image/webp", ".webp")

    app.mount(
        "/media", StaticFiles(directory=settings.app.MEDIA_ROOT, check_dir=False), name="media"
    )

    for router in (
        health.router,
        auth.router,
        catalog.router,
        favorites.router,
        internal_sync.router,
        products.router,
        raw_posts.router,
        categories.router,
        sync.router,
        seller_settings.router,
        stats.router,
        banners.router,
        moderators.router,
        contacts.router,
        seller_invites.router,
        invite_redeem.router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    setup_dishka(build_container(), app)
    return app
