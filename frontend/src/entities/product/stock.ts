import type { Product } from './types'

type StockFields = Pick<Product, 'availability' | 'quantity'>

/**
 * A product can't be added to the cart when the seller has explicitly
 * marked it "Нет в наличии" — that choice wins even if a stray quantity
 * number is still sitting on the row — or when tracked stock has hit zero.
 * "На заказ" stays addable (that's the point of a pre-order), capped by
 * `maxCartQuantity` below like any other tracked quantity.
 */
export function isOutOfStock(product: StockFields): boolean {
  if (product.availability === 'out_of_stock') return true
  return product.quantity !== null && product.quantity <= 0
}

/** How many of this product the cart can hold — `null` means untracked
 * (no cap), `0` means it can't be added at all. Mirrors the backend's own
 * checkout validation (`OrderService.checkout`), which enforces `quantity`
 * as a hard ceiling independent of the `availability` label — so capping
 * the same way here means the cart never lets you add more than checkout
 * will actually accept. */
export function maxCartQuantity(product: StockFields): number | null {
  if (isOutOfStock(product)) return 0
  return product.quantity
}

/**
 * Only a genuinely in-stock, tracked quantity is worth surfacing to a
 * customer as "· N шт." — next to "Нет в наличии"/"На заказ" a number reads
 * as self-contradictory, since the label already says this isn't simply
 * available off the shelf.
 */
export function shouldShowQuantity(product: StockFields): boolean {
  return product.availability === 'in_stock' && (product.quantity ?? 0) > 0
}
