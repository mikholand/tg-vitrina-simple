import { z } from 'zod'

const orderItemSchema = z.object({
  id: z.number(),
  product_id: z.number().nullable(),
  product_name: z.string(),
  sku: z.string().nullable(),
  price: z.string(),
  currency: z.string(),
  quantity: z.number(),
  // Snapshot of the product's first photo at checkout (a /media/... URL).
  // May point at a file deleted together with its product since — the UI
  // falls back to a placeholder on load error (OrderItemThumb.vue).
  photo_path: z.string().nullable().default(null),
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

const orderCustomerSchema = z.object({
  id: z.number(),
  tg_username: z.string().nullable(),
  tg_first_name: z.string().nullable(),
  tg_last_name: z.string().nullable(),
})

// Seller-only view (`GET /seller/orders`): adds the buyer's Telegram
// identity, null for a guest checkout from the website.
export const sellerOrderSchema = orderSchema.extend({
  customer: orderCustomerSchema.nullable().default(null),
})

export const paginatedSellerOrderSchema = paginatedOrderSchema.extend({
  items: z.array(sellerOrderSchema),
})
