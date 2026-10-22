from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.config import Settings
from app.core.start_param import encode_start_param


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.telegram.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


class BotClient:
    def __init__(self, bot: Bot, mini_app_short_name: str) -> None:
        self._bot = bot
        self._mini_app_short_name = mini_app_short_name
        self._username: str | None = None

    async def username(self) -> str:
        if self._username is None:
            me = await self._bot.get_me()
            if me.username is None:
                raise RuntimeError("Bot has no username; cannot build Mini App deep links")
            self._username = me.username
        return self._username

    async def mini_app_url(self, start_param: str) -> str:
        """Builds a `startapp` deep link that actually launches the Mini App.

        A bare `https://t.me/<bot>?startapp=...` only opens the bot's chat
        unless the bot's default Menu Button is itself a Web App — it does
        NOT launch a Mini App registered as a BotFather Direct Link. Direct
        Links require the short name in the path:
        `https://t.me/<bot>/<short_name>?startapp=...` (see
        `settings.app.MINI_APP_SHORT_NAME`). Used for product share links,
        invite links, and the "Открыть в витрине" channel-post button below.
        """
        username = await self.username()
        return f"https://t.me/{username}/{self._mini_app_short_name}?startapp={start_param}"

    async def product_mini_app_url(self, product_id: int) -> str:
        """Share link for a single product — the `startapp` value is just
        `/product/<id>` base64url-encoded (see `app/core/start_param.py`),
        decoded by the frontend router guard straight into that route."""
        return await self.mini_app_url(encode_start_param(f"/product/{product_id}"))

    async def invite_mini_app_url(self, token: str) -> str:
        """Team invite link — `startapp` encodes `/invite/<token>`; the
        frontend guard recognizes that prefix specially (redeems the invite
        via an API call, it's not an actual page route) rather than
        navigating to it like a product link."""
        return await self.mini_app_url(encode_start_param(f"/invite/{token}"))

    def _mini_app_keyboard(self, url: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Открыть в витрине", url=url))
        return builder.as_markup()

    async def publish_product(
        self, channel_id: int, product_id: int, caption: str, photo_path: str | None
    ) -> int:
        url = await self.product_mini_app_url(product_id)
        keyboard = self._mini_app_keyboard(url)

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
