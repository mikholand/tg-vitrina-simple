export interface CheckoutItemPayload {
  product_id: number
  quantity: number
}

export interface CheckoutPayload {
  items: CheckoutItemPayload[]
  comment?: string | null
}

export interface OrderItem {
  id: number
  product_id: number | null
  product_name: string
  price: string
  currency: string
  quantity: number
}

export interface Order {
  id: number
  customer_id: number | null
  total: string
  currency: string
  comment: string | null
  status: string
  notified: boolean
  created_at: string
  items: OrderItem[]
}
