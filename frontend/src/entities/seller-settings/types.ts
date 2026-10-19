export interface SellerSettings {
  store_name: string
  store_description: string
  store_logo: string | null
  store_contact_tg: string | null
  telegram_channel_id: number
  extractor_configured: boolean
}

export interface SellerSettingsUpdatePayload {
  name?: string
  description?: string
  contact_tg?: string
}

export interface TopProduct {
  id: number
  name: string
  views_total: number
}

/** Matches the backend's `period` query param on `GET /seller/stats`. */
export type StatsPeriod = 'all' | '7d' | '30d'

export interface SellerStats {
  store_views_total: number
  product_views_total: number
  top_products: TopProduct[]
}
