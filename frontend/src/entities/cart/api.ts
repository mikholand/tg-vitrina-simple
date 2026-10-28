import { http } from '@shared/api/http'
import type { Paginated } from '@shared/types/pagination'
import { orderSchema, paginatedOrderSchema, paginatedSellerOrderSchema, sellerOrderSchema } from './schema'
import type { CheckoutPayload, Order, OrderStatus, SellerOrder } from './types'

/** Submits the cart as an order. Requires an authenticated customer (see
 * `CurrentUser` on the backend's `/catalog/orders`) — the cart itself is
 * built up anonymously/locally, but checkout is not. */
export async function checkout(payload: CheckoutPayload): Promise<Order> {
  const { data } = await http.post('/catalog/orders', payload)
  return orderSchema.parse(data)
}

/** A logged-in customer's own order history — guest checkouts
 * (`customer_id` null) never show up here, see the backend's
 * `OrderRepository.list_for_customer`. */
export async function getMyOrders(limit = 20, offset = 0): Promise<Paginated<Order>> {
  const { data } = await http.get('/catalog/orders/my', { params: { limit, offset } })
  return paginatedOrderSchema.parse(data)
}

/** Every order in the shop, newest first, optionally narrowed to some
 * statuses (sent as a repeated `?status=` param — axios's default
 * `status[]=` bracket form isn't what FastAPI's list query expects). */
export async function getSellerOrders(
  statuses: OrderStatus[] = [],
  limit = 20,
  offset = 0,
): Promise<Paginated<SellerOrder>> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  for (const status of statuses) params.append('status', status)
  const { data } = await http.get('/seller/orders', { params })
  return paginatedSellerOrderSchema.parse(data)
}

export async function changeOrderStatus(id: number, status: OrderStatus): Promise<SellerOrder> {
  const { data } = await http.patch(`/seller/orders/${id}/status`, { status })
  return sellerOrderSchema.parse(data)
}
