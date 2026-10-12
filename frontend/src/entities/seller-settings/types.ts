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

export interface SellerStats {
  store_views_total: number
  store_views_today: number
  top_products: TopProduct[]
}
