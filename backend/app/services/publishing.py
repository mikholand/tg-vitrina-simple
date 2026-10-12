from app.clients.bot import BotClient
from app.core.config import Settings
from app.entities.product import Product
from app.shared.media import media_abs_path


def _format_caption(product: Product) -> str:
    lines = [f"<b>{product.name}</b>"]
    if product.price is not None:
        lines.append(f"{product.price} {product.currency}")
    if product.description:
        lines.append(product.description)
    return "\n\n".join(lines)


class PublishingService:
    def __init__(self, bot_client: BotClient, settings: Settings) -> None:
        self._bot_client = bot_client
        self._settings = settings

    async def publish_to_channel(self, product: Product) -> int:
        photo_path = media_abs_path(self._settings, product.photo_paths[0]) if product.photo_paths else None
        caption = _format_caption(product)
        return await self._bot_client.publish_product(
            channel_id=self._settings.store.TELEGRAM_CHANNEL_ID,
            product_id=product.id,
            caption=caption,
            photo_path=str(photo_path) if photo_path else None,
        )
