from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.contact import MAX_CONTACTS, Contact, ContactType


class ContactLimitExceededError(Exception):
    pass


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).order_by(Contact.sort_order, Contact.id)
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[Contact]:
        result = await self._session.execute(
            select(Contact).where(Contact.is_active).order_by(Contact.sort_order, Contact.id)
        )
        return list(result.scalars().all())

    async def get(self, contact_id: int) -> Contact | None:
        return await self._session.get(Contact, contact_id)

    async def create(self, label: str, type_: ContactType, value: str, sort_order: int) -> Contact:
        existing = await self.list_all()
        if len(existing) >= MAX_CONTACTS:
            raise ContactLimitExceededError(f"at most {MAX_CONTACTS} contacts are allowed")
        contact = Contact(
            label=label, type=type_, value=value, sort_order=sort_order, is_active=True
        )
        self._session.add(contact)
        await self._session.flush()
        return contact

    async def update(
        self,
        contact: Contact,
        label: str | None = None,
        type_: ContactType | None = None,
        value: str | None = None,
        sort_order: int | None = None,
        is_active: bool | None = None,
    ) -> Contact:
        if label is not None:
            contact.label = label
        if type_ is not None:
            contact.type = type_
        if value is not None:
            contact.value = value
        if sort_order is not None:
            contact.sort_order = sort_order
        if is_active is not None:
            contact.is_active = is_active
        await self._session.flush()
        return contact

    async def delete(self, contact: Contact) -> None:
        await self._session.delete(contact)
        await self._session.flush()
