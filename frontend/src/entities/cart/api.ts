import { http } from '@shared/api/http'
import type { Paginated } from '@shared/types/pagination'
import { orderSchema, paginatedOrderSchema } from './schema'
import type { CheckoutPayload, Order } from './types'

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
