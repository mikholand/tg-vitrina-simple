from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger("telegram.commands")


def build_commands_router(settings: Settings) -> Router:
    """Handles direct messages to the bot (as opposed to the channel-post
    router, which only sees posts in the source channel). Currently just
    /start, replying with a greeting and — when WEBAPP_URL is configured — a
    button that opens the Mini App storefront.
    """
    router = Router(name="commands")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        store_name = settings.store.STORE_NAME
        keyboard: InlineKeyboardMarkup | None = None
        if settings.app.WEBAPP_URL:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Открыть магазин",
                            web_app=WebAppInfo(url=settings.app.WEBAPP_URL),
                        )
                    ]
                ]
            )

        await message.answer(
            f"Добро пожаловать в {store_name}! Нажмите кнопку ниже, чтобы открыть каталог."
            if keyboard is not None
            else f"Добро пожаловать в {store_name}!",
            reply_markup=keyboard,
        )
        logger.info("bot_start_command", user_id=message.from_user.id if message.from_user else None)

    return router
