import type { OrderStatus } from './types'

export const orderStatusLabels: Record<OrderStatus, string> = {
  new: 'Новый',
  accepted: 'Принят',
  shipped: 'Отправлен',
  completed: 'Выполнен',
  cancelled: 'Отменён',
}

// Only "new" is solid — it's the one that needs someone to act on it, in
// the seller's list most of all; the rest are soft tints that just tell
// the stages apart. Amber/green text uses Tailwind's -700 shades rather
// than --sf-warning/--sf-success: those are fill colors and fall well
// short of readable contrast as small text on their own -soft tints.
const statusClasses: Record<OrderStatus, string> = {
  new: 'bg-sf-accent text-sf-accent-ink',
  accepted: 'bg-sf-warning-soft text-amber-700',
  shipped: 'bg-sf-soft text-sf-accent',
  completed: 'bg-sf-success-soft text-green-700',
  cancelled: 'bg-sf-surface text-sf-muted',
}

function isKnown(status: string): status is OrderStatus {
  return status in orderStatusLabels
}

// Falls back to the raw value / a neutral pill for a status the backend
// knows and this build doesn't yet, rather than rendering nothing.
export function orderStatusLabel(status: string): string {
  return isKnown(status) ? orderStatusLabels[status] : status
}

export function orderStatusClass(status: string): string {
  return isKnown(status) ? statusClasses[status] : statusClasses.cancelled
}
