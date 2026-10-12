import asyncio

from aiogram import Bot, Dispatcher

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.di.container import build_container
from app.telegram.handlers import build_channel_router

logger = get_logger("telegram.main")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.app.LOG_LEVEL)

    container = build_container()
    bot = await container.get(Bot)

    dispatcher = Dispatcher()
    dispatcher.include_router(build_channel_router(container, settings, bot))

    logger.info("telegram_bot_starting", channel_id=settings.store.TELEGRAM_CHANNEL_ID)
    try:
        await dispatcher.start_polling(bot, allowed_updates=["channel_post", "edited_channel_post"])
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
