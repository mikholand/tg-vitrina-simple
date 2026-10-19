from pydantic import BaseModel, ConfigDict, Field

from app.entities.contact import ContactType


def contact_url(contact_type: ContactType, value: str) -> str:
    """Готовая ссылка для кнопки: чат в Telegram или набор номера.

    Собирается на сервере, не в вёрстке — одно правило и для кабинета, и
    для витрины, вместо двух копий, которые могут разъехаться.
    """
    value = value.strip()
    if contact_type is ContactType.PHONE:
        # `tel:` не переносит пробелы и скобки, в которых пишут номер.
        digits = "".join(c for c in value if c.isdigit() or c == "+")
        return f"tel:{digits}"
    if value.startswith("http"):
        return value
    return f"https://t.me/{value.lstrip('@')}"


class ContactSchema(BaseModel):
    """Менеджер магазина в кабинете продавца."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    type: ContactType
    value: str
    sort_order: int
    is_active: bool


class ContactCreateSchema(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    type: ContactType
    value: str = Field(min_length=1, max_length=200)


class ContactUpdateSchema(BaseModel):
    """PATCH semantics — every field is optional and only applied when sent."""

    label: str | None = Field(default=None, min_length=1, max_length=100)
    type: ContactType | None = None
    value: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class PublicContactSchema(BaseModel):
    """Менеджер магазина в шторке «Написать продавцу»."""

    id: int
    label: str
    type: ContactType
    value: str
    #: Куда ведёт нажатие (`https://t.me/...` или `tel:...`).
    url: str
