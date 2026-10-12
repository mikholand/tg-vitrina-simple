from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.config import Settings


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.telegram.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


class BotClient:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._username: str | None = None

    async def username(self) -> str:
        if self._username is None:
            me = await self._bot.get_me()
            if me.username is None:
                raise RuntimeError("Bot has no username; cannot build Mini App deep links")
            self._username = me.username
        return self._username

    def _mini_app_keyboard(self, product_id: int, bot_username: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="Открыть в витрине",
                url=f"https://t.me/{bot_username}?startapp=product_{product_id}",
            )
        )
        return builder.as_markup()

    async def publish_product(
        self, channel_id: int, product_id: int, caption: str, photo_path: str | None
    ) -> int:
        bot_username = await self.username()
        keyboard = self._mini_app_keyboard(product_id, bot_username)

        if photo_path:
            message = await self._bot.send_photo(
                chat_id=channel_id,
                photo=FSInputFile(photo_path),
                caption=caption,
                reply_markup=keyboard,
            )
        else:
            message = await self._bot.send_message(
                chat_id=channel_id, text=caption, reply_markup=keyboard
            )
        return message.message_id
