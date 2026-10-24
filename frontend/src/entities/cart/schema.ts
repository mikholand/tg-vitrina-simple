import { z } from 'zod'

const orderItemSchema = z.object({
  id: z.number(),
  product_id: z.number().nullable(),
  product_name: z.string(),
  price: z.string(),
  currency: z.string(),
  quantity: z.number(),
})

export const orderSchema = z.object({
  id: z.number(),
  customer_id: z.number().nullable(),
  total: z.string(),
  currency: z.string(),
  comment: z.string().nullable(),
  status: z.string(),
  notified: z.boolean(),
  created_at: z.string(),
  items: z.array(orderItemSchema),
})
