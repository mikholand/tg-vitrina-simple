import { z } from 'zod'

const orderItemSchema = z.object({
  id: z.number(),
  product_id: z.number().nullable(),
  product_name: z.string(),
  sku: z.string().nullable(),
  price: z.string(),
  currency: z.string(),
  quantity: z.number(),
})

export const orderSchema = z.object({
  id: z.number(),
  customer_id: z.number().nullable(),
  contact_name: z.string().nullable(),
  contact_phone: z.string().nullable(),
  total: z.string(),
  currency: z.string(),
  comment: z.string().nullable(),
  status: z.string(),
  notified: z.boolean(),
  created_at: z.string(),
  items: z.array(orderItemSchema),
})

export const paginatedOrderSchema = z.object({
  items: z.array(orderSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
})
