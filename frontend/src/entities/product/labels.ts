import type { ProductAvailability, ProductStatus } from './types'

/** Russian labels for storefront display — mirrors tg-vitrina's wording. */
export const availabilityLabels: Record<ProductAvailability, string> = {
  in_stock: 'В наличии',
  on_order: 'На заказ',
  out_of_stock: 'Нет в наличии',
  unknown: '',
}

/** Chip background/text classes per availability — same palette tg-vitrina uses. */
export const availabilityChipClasses: Record<ProductAvailability, string> = {
  in_stock: 'bg-sf-success-soft text-sf-success',
  on_order: 'bg-sf-warning-soft text-sf-warning',
  out_of_stock: 'bg-sf-danger-soft text-sf-danger',
  unknown: 'bg-sf-line text-sf-muted',
}

/** Russian labels for seller-cabinet product status — tg-vitrina's ProductRow wording. */
export const productStatusLabels: Record<ProductStatus, string> = {
  draft: 'Черновик',
  published: 'Опубликован',
  hidden: 'Скрыт',
}

/** Chip classes per product status, same soft-tint palette as availability chips. */
export const productStatusChipClasses: Record<ProductStatus, string> = {
  draft: 'bg-sf-warning-soft text-sf-warning',
  published: 'bg-sf-success-soft text-sf-success',
  hidden: 'bg-sf-line text-sf-muted',
}

function currencySymbol(currency: string): string {
  switch (currency.toUpperCase()) {
    case 'RUB':
      return '₽'
    case 'USD':
      return '$'
    case 'EUR':
      return '€'
    default:
      return currency
  }
}

/** Formats a price string with a RU thousands separator and currency symbol. */
export function formatPrice(price: string | null, currency: string): string {
  if (!price) return 'Цена по запросу'
  const value = Number(price)
  if (Number.isNaN(value)) return `${price} ${currency}`
  return `${new Intl.NumberFormat('ru-RU').format(value)} ${currencySymbol(currency)}`
}
