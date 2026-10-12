import type { RawPostStatus } from './types'

/** Russian labels for raw-post status, shown on the seller's "Посты" page. */
export const rawPostStatusLabels: Record<RawPostStatus, string> = {
  new: 'Новый',
  extracted: 'Распознано',
  failed: 'Ошибка',
}

/** Chip classes per raw-post status, same soft-tint palette as product chips. */
export const rawPostStatusChipClasses: Record<RawPostStatus, string> = {
  new: 'bg-sf-soft text-sf-accent',
  extracted: 'bg-sf-success-soft text-sf-success',
  failed: 'bg-sf-danger-soft text-sf-danger',
}
