import { z } from 'zod'

export const userRoleSchema = z.enum(['admin', 'seller', 'customer'])

export const loginResponseSchema = z.object({
  token: z.string(),
  user_id: z.number(),
  role: userRoleSchema,
})

export const meResponseSchema = z.object({
  id: z.number(),
  tg_username: z.string().nullable(),
  tg_first_name: z.string().nullable(),
  tg_last_name: z.string().nullable(),
  role: userRoleSchema,
})
