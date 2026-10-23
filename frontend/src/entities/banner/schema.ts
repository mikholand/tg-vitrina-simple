import { z } from 'zod'

export const bannerSchema = z.object({
  id: z.number(),
  image_path_mobile: z.string(),
  image_path_desktop: z.string().nullable(),
  link_url: z.string().nullable(),
  sort_order: z.number(),
})

export const bannerListSchema = z.array(bannerSchema)
