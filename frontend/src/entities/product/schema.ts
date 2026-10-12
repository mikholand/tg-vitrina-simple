import { z } from 'zod'

export const productAvailabilitySchema = z.enum(['in_stock', 'on_order', 'out_of_stock', 'unknown'])
export const productStatusSchema = z.enum(['draft', 'published', 'hidden'])

export const productSchema = z.object({
  id: z.number(),
  name: z.string(),
  price: z.string().nullable(),
  currency: z.string(),
  description: z.string().nullable(),
  sku: z.string().nullable(),
  availability: productAvailabilitySchema,
  quantity: z.number().nullable(),
  photo_paths: z.array(z.string()),
  status: productStatusSchema,
  edited_by_seller: z.boolean(),
  publish_to_channel: z.boolean(),
  views_total: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
  category_ids: z.array(z.number()),
})

export const paginatedProductSchema = z.object({
  items: z.array(productSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
})
