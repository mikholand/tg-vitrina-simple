import { http } from '@shared/api/http'
import { contactListSchema, contactSchema, publicContactListSchema } from './schema'
import type { Contact, ContactCreatePayload, ContactUpdatePayload, PublicContact } from './types'

export async function getCatalogContacts(): Promise<PublicContact[]> {
  const { data } = await http.get('/catalog/contacts')
  return publicContactListSchema.parse(data)
}

export async function getSellerContacts(): Promise<Contact[]> {
  const { data } = await http.get('/seller/contacts')
  return contactListSchema.parse(data)
}

export async function createContact(payload: ContactCreatePayload): Promise<Contact> {
  const { data } = await http.post('/seller/contacts', payload)
  return contactSchema.parse(data)
}

export async function updateContact(id: number, payload: ContactUpdatePayload): Promise<Contact> {
  const { data } = await http.patch(`/seller/contacts/${id}`, payload)
  return contactSchema.parse(data)
}

export async function deleteContact(id: number): Promise<void> {
  await http.delete(`/seller/contacts/${id}`)
}
