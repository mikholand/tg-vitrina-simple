import { z } from 'zod'

export const bannerSchema = z.object({
  id: z.number(),
  image_path: z.string(),
  link_url: z.string().nullable(),
  sort_order: z.number(),
})

export const bannerListSchema = z.array(bannerSchema)
