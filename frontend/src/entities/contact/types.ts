export type ContactType = 'telegram' | 'phone'

export interface Contact {
  id: number
  label: string
  type: ContactType
  value: string
  sort_order: number
  is_active: boolean
}

export interface ContactCreatePayload {
  label: string
  type: ContactType
  value: string
}

export interface ContactUpdatePayload {
  label?: string
  type?: ContactType
  value?: string
  sort_order?: number
  is_active?: boolean
}

/** Менеджер магазина в шторке «Написать продавцу» — публичный, без sort_order/is_active. */
export interface PublicContact {
  id: number
  label: string
  type: ContactType
  value: string
  /** Куда ведёт нажатие (`https://t.me/...` или `tel:...`). */
  url: string
}
