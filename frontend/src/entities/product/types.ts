export type ProductAvailability = 'in_stock' | 'on_order' | 'out_of_stock' | 'unknown'
export type ProductStatus = 'draft' | 'published' | 'hidden'

export interface Product {
  id: number
  name: string
  price: string | null
  currency: string
  description: string | null
  sku: string | null
  availability: ProductAvailability
  quantity: number | null
  photo_paths: string[]
  video_path: string | null
  status: ProductStatus
  edited_by_seller: boolean
  publish_to_channel: boolean
  views_total: number
  created_at: string
  updated_at: string
  category_ids: number[]
  /** Mini App deep link (`https://t.me/<bot>?startapp=product_<id>`) for the
   *  "Поделиться" button — only populated on `GET /catalog/products/{id}`
   *  (the detail endpoint), null everywhere else this type is reused
   *  (catalog/seller list endpoints). */
  share_url: string | null
}

export interface CatalogProductListParams {
  category_id?: number
  search?: string
  limit?: number
  offset?: number
}

export interface SellerProductListParams {
  status?: ProductStatus
  q?: string
  limit?: number
  offset?: number
}

export interface SellerProductCreate {
  name: string
  price?: string | null
  currency?: string
  description?: string | null
  sku?: string | null
  availability?: ProductAvailability
  quantity?: number | null
  category_ids?: number[]
}

export interface SellerProductPatch {
  name?: string
  price?: string | null
  currency?: string
  description?: string | null
  sku?: string | null
  availability?: ProductAvailability
  quantity?: number | null
  category_ids?: number[]
  publish_to_channel?: boolean
}
