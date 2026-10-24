from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from dishka import AsyncContainer

from app.core.config import Settings
from app.core.logging import get_logger
from app.entities.user import UserRole
from app.repositories.store_profile import StoreProfileRepository
from app.repositories.user import UserRepository

logger = get_logger("telegram.commands")


async def try_configure_order_chat(container: AsyncContainer, sender_id: int, chat_id: int) -> bool:
    """Core of the admin-only `/setorderchat` command, pulled out of the
    aiogram handler below so it's unit-testable without simulating a
    `Message`/`Dispatcher` round-trip. Returns whether `sender_id` was
    authorized (and, if so, the chat was persisted) — the trust anchor is
    the DB `User.role` check here, which only ever gets set to ADMIN via
    `SUPER_ADMIN_IDS`-driven auto-promotion at Mini App login (see
    `telegram_auth.py`); nothing about the caller-supplied `sender_id`/
    `chat_id` themselves is trusted on its own.
    """
    async with container() as request_container:
        user_repository = await request_container.get(UserRepository)
        user = await user_repository.get(sender_id)
        if user is None or user.role != UserRole.ADMIN:
            logger.warning("set_order_chat_denied", user_id=sender_id)
            return False

        store_profile_repository = await request_container.get(StoreProfileRepository)
        await store_profile_repository.set_order_notification_chat(chat_id)

    logger.info("set_order_chat_configured", user_id=sender_id, chat_id=chat_id)
    return True


def build_commands_router(container: AsyncContainer, settings: Settings) -> Router:
    """Handles direct messages to the bot (as opposed to the channel-post
    router, which only sees posts in the source channel): /start, and the
    admin-only /setorderchat below.
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

    @router.message(Command("setorderchat"))
    async def on_set_order_chat(message: Message) -> None:
        """Points checkout order notifications (see `OrderService._notify`)
        at whichever chat this is run in — a group, a channel, or the
        admin's own DM with the bot."""
        sender_id = message.from_user.id if message.from_user else None
        if sender_id is None:
            return

        authorized = await try_configure_order_chat(container, sender_id, message.chat.id)
        if not authorized:
            await message.answer("Эта команда доступна только администратору магазина.")
            return

        await message.answer("Готово — заказы из витрины теперь будут приходить в этот чат.")

    return router
