export interface Banner {
  id: number
  image_path_mobile: string
  image_path_desktop: string | null
  link_url: string | null
  sort_order: number
}

export interface BannerUpdatePayload {
  link_url?: string | null
  sort_order?: number
}
