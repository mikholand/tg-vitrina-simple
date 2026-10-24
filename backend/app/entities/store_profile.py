from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin

STORE_PROFILE_SINGLETON_ID = 1


class StoreProfile(Base, TimestampMixin):
    """Singleton row (id=1) holding the seller-editable store identity —
    name/description/logo/contact. There is no `shops` table to hang this
    off of (single-tenant deployment), same convention as `SyncState`.

    Seeded lazily from the `STORE_*` env vars the first time it's read (see
    `StoreProfileRepository.get`), so an existing deployment's env-configured
    identity survives the switch to DB-backed, admin-editable settings.
    """

    __tablename__ = "store_profile"

    id: Mapped[int] = mapped_column(primary_key=True, default=STORE_PROFILE_SINGLETON_ID)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    logo: Mapped[str | None] = mapped_column(String(300))
    contact_tg: Mapped[str | None] = mapped_column(String(100))
    # Telegram chat id a checkout's order notification is sent to. Set only
    # via the admin-only `/setorderchat` bot command (see
    # `app/telegram/commands.py`) — not exposed on the settings PATCH form —
    # since whoever runs that command does so from inside the target chat
    # itself, which is the whole point: no risk of mistyping a chat id by
    # hand. Null until an admin runs the command once.
    order_notification_chat_id: Mapped[int | None] = mapped_column(BigInteger)
