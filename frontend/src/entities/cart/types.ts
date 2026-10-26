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
}

export interface Order {
  id: number
  customer_id: number | null
  contact_name: string | null
  contact_phone: string | null
  total: string
  currency: string
  comment: string | null
  status: string
  notified: boolean
  created_at: string
  items: OrderItem[]
}
