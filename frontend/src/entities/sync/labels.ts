import type { SyncStatus } from './types'

/** Russian labels for the channel-sync status shown on the seller dashboard. */
export const syncStatusLabels: Record<SyncStatus, string> = {
  idle: 'Не запущена',
  requested: 'Запрошена',
  running: 'Идёт',
  done: 'Готово',
  failed: 'Ошибка',
  interrupted: 'Прервана',
}

/** Chip classes per sync status, same soft-tint palette as product chips. */
export const syncStatusChipClasses: Record<SyncStatus, string> = {
  idle: 'bg-sf-line text-sf-muted',
  requested: 'bg-sf-soft text-sf-accent',
  running: 'bg-sf-soft text-sf-accent',
  done: 'bg-sf-success-soft text-sf-success',
  failed: 'bg-sf-danger-soft text-sf-danger',
  interrupted: 'bg-sf-warning-soft text-sf-warning',
}
