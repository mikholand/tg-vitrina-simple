export interface Banner {
  id: number
  image_path: string
  link_url: string | null
  sort_order: number
}

export interface BannerUpdatePayload {
  link_url?: string | null
  sort_order?: number
}
