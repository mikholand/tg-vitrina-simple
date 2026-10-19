import enum

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base, TimestampMixin

# Шторка выбора менеджера должна помещаться на экран телефона — больше
# десятка контактов это уже не выбор, а список, который никто не дочитает.
MAX_CONTACTS = 10


class ContactType(enum.StrEnum):
    """Как открывается контакт продавца: чат в Telegram или звонок.

    Явный тип, не «угадать по значению» — номер и юзернейм разворачиваются
    в разные ссылки (`tel:` против `https://t.me/`).
    """

    TELEGRAM = "telegram"
    PHONE = "phone"


class Contact(Base, TimestampMixin):
    """Один из менеджеров магазина: подпись, тип и значение.

    Single-tenant — без shop_id, как Banner: во всём приложении один магазин.
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #: Что видит покупатель в шторке выбора: «Анна, продажи», «Сервис».
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[ContactType] = mapped_column(
        Enum(ContactType, native_enum=False, length=20), nullable=False
    )
    #: Юзернейм (@nova_market) или номер (+7 999 …).
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
