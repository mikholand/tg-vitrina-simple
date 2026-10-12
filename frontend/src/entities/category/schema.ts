import { z } from 'zod'

export const categorySchema = z.object({
  id: z.number(),
  parent_id: z.number().nullable(),
  name: z.string(),
  code: z.string(),
  sort_order: z.number(),
  depth: z.number(),
  is_fallback: z.boolean(),
  is_hidden: z.boolean(),
})

export const categoryListSchema = z.array(categorySchema)
