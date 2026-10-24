import { http } from '@shared/api/http'
import { orderSchema } from './schema'
import type { CheckoutPayload, Order } from './types'

/** Submits the cart as an order. Requires an authenticated customer (see
 * `CurrentUser` on the backend's `/catalog/orders`) — the cart itself is
 * built up anonymously/locally, but checkout is not. */
export async function checkout(payload: CheckoutPayload): Promise<Order> {
  const { data } = await http.post('/catalog/orders', payload)
  return orderSchema.parse(data)
}
