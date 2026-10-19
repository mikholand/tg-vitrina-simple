import { z } from 'zod'

const contactTypeSchema = z.union([z.literal('telegram'), z.literal('phone')])

export const contactSchema = z.object({
  id: z.number(),
  label: z.string(),
  type: contactTypeSchema,
  value: z.string(),
  sort_order: z.number(),
  is_active: z.boolean(),
})

export const contactListSchema = z.array(contactSchema)

export const publicContactSchema = z.object({
  id: z.number(),
  label: z.string(),
  type: contactTypeSchema,
  value: z.string(),
  url: z.string(),
})

export const publicContactListSchema = z.array(publicContactSchema)
