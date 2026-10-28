export interface CheckoutItemPayload {
  product_id: number
  quantity: number
}

export interface CheckoutPayload {
  items: CheckoutItemPayload[]
  comment?: string | null
  // Required by the backend when there's no Telegram session (checkout from
  // the plain website) — see `OrderService.checkout`.
  contact_name?: string | null
  contact_phone?: string | null
}

export interface OrderItem {
  id: number
  product_id: number | null
  product_name: string
  sku: string | null
  price: string
  currency: string
  quantity: number
  photo_path: string | null
}

export interface Order {
  id: number
  customer_id: number | null
  contact_name: string | null
  contact_phone: string | null
  total: string
  currency: string
  comment: string | null
  // Plain string, not OrderStatus: the schema parses it as z.string() so a
  // status added on the backend first doesn't make every order list fail to
  // parse — labels.ts falls back to the raw value for unknown ones.
  status: string
  notified: boolean
  created_at: string
  items: OrderItem[]
}

/** Mirrors the backend's `OrderStatus` (app/entities/order.py). */
export type OrderStatus = 'new' | 'accepted' | 'shipped' | 'completed' | 'cancelled'

export interface OrderCustomer {
  id: number
  tg_username: string | null
  tg_first_name: string | null
  tg_last_name: string | null
}

export interface SellerOrder extends Order {
  customer: OrderCustomer | null
}
