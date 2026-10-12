import { z } from 'zod'

export const rawPostStatusSchema = z.enum(['new', 'extracted', 'failed'])

export const rawPostSchema = z.object({
  id: z.number(),
  channel_id: z.number(),
  message_id: z.number(),
  media_group_id: z.number().nullable(),
  raw_text: z.string().nullable(),
  photo_paths: z.array(z.string()),
  posted_at: z.string(),
  status: rawPostStatusSchema,
  product_id: z.number().nullable(),
  created_at: z.string(),
})

export const paginatedRawPostSchema = z.object({
  items: z.array(rawPostSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
})
