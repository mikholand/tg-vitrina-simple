from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentSeller
from app.dto.contact import ContactCreateSchema, ContactSchema, ContactUpdateSchema
from app.repositories.contact import ContactLimitExceededError, ContactRepository

router = APIRouter(route_class=DishkaRoute, prefix="/seller/contacts", tags=["seller"])

# Owner-only (CurrentSeller, not CurrentStaff) — matches the frontend's own
# `requiresOwner: true` on `/seller/contacts` (router/index.ts). Previously
# this was CurrentStaff, which let a moderator manage contacts over the API
# even though the Mini App's own router guard never let them reach the page.


@router.get("")
async def list_contacts(
    _: CurrentSeller, contact_repository: FromDishka[ContactRepository]
) -> list[ContactSchema]:
    contacts = await contact_repository.list_all()
    return [ContactSchema.model_validate(c) for c in contacts]


@router.post("")
async def create_contact(
    payload: ContactCreateSchema,
    _: CurrentSeller,
    contact_repository: FromDishka[ContactRepository],
) -> ContactSchema:
    existing = await contact_repository.list_all()
    try:
        contact = await contact_repository.create(
            payload.label.strip(), payload.type, payload.value.strip(), len(existing)
        )
    except ContactLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ContactSchema.model_validate(contact)


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: int,
    payload: ContactUpdateSchema,
    _: CurrentSeller,
    contact_repository: FromDishka[ContactRepository],
) -> ContactSchema:
    contact = await contact_repository.get(contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
    contact = await contact_repository.update(
        contact,
        label=payload.label.strip() if payload.label is not None else None,
        type_=payload.type,
        value=payload.value.strip() if payload.value is not None else None,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    return ContactSchema.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    _: CurrentSeller,
    contact_repository: FromDishka[ContactRepository],
) -> None:
    contact = await contact_repository.get(contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
    await contact_repository.delete(contact)
