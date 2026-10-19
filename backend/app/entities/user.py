import enum

from sqlalchemy import BigInteger, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin


class UserRole(enum.StrEnum):
    """Roles within this single store. No cross-shop concept — just one app."""

    ADMIN = "admin"
    SELLER = "seller"
    MODERATOR = "moderator"
    CUSTOMER = "customer"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id
    tg_username: Mapped[str | None] = mapped_column(String(64))
    tg_first_name: Mapped[str | None] = mapped_column(String(128))
    tg_last_name: Mapped[str | None] = mapped_column(String(128))
    # Telegram only populates this for Mini Apps launched from the attachment
    # menu — null for the common "open via bot menu button" case, so the
    # frontend always needs a letter-avatar fallback. Refreshed on every
    # login (see UserRepository.upsert_from_telegram), since Telegram's photo
    # URLs can rotate/expire.
    tg_photo_url: Mapped[str | None] = mapped_column(String(512))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), default=UserRole.CUSTOMER, nullable=False
    )
