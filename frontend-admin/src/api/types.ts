/** 与后端统一响应体 / 业务模型对齐的类型定义。 */

export interface ApiResult<T = unknown> {
  code: number
  message: string
  data: T | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface AdminInfo {
  id: number
  username: string
  name: string
}

export interface LoginResult {
  token: string
  token_type: string
  expires_in: number
  admin: AdminInfo
}

export interface Category {
  id: number
  name: string
  sort_order: number
  product_count: number
  created_at?: string | null
}

export type ProductStatus = 'on_sale' | 'off_shelf'

/** 商品规格：单维度互斥，客户下单时单选一个。 */
export interface ProductVariant {
  id: number
  name: string
  sku?: string | null
  price: number
  image_url?: string | null
  status: ProductStatus
}

/** 规格入参：保存时整体替换，不需要携带 id。 */
export interface ProductVariantInput {
  name: string
  sku?: string | null
  price: number
  image_url?: string | null
  status: ProductStatus
}

export interface Product {
  id: number
  name: string
  sku?: string | null
  category_id?: number | null
  category_name?: string | null
  /** 有规格时该价格为最低规格价，即对外起价 */
  price: number
  unit: string
  image_url?: string | null
  description?: string | null
  status: ProductStatus
  variants?: ProductVariant[]
  variant_count?: number
  created_at?: string | null
  updated_at?: string | null
}

export interface ProductBrief {
  id: number
  name: string
  price: number
  unit: string
  image_url?: string | null
  description?: string | null
  category_id?: number | null
  category_name?: string | null
}

export interface PermissionTemplate {
  id: number
  name: string
  description?: string | null
  is_active: boolean
  product_count: number
  product_ids: number[]
  created_at?: string | null
  updated_at?: string | null
}

export interface TemplateOption {
  id: number
  name: string
  description?: string | null
  product_count: number
}

export type LinkDerivedStatus =
  | 'unused'
  | 'in_use'
  | 'expired'
  | 'exhausted'
  | 'disabled'
  | 'voided'

export interface TempLink {
  id: number
  token: string
  url: string
  template_id: number
  template_name?: string | null
  remark?: string | null
  expire_at?: string | null
  max_uses?: number | null
  used_count: number
  remaining_uses?: number | null
  is_single_use: boolean
  status: string
  derived_status: LinkDerivedStatus
  status_label: string
  created_at?: string | null
  last_accessed_at?: string | null
}

export interface LinkCreatePayload {
  template_id: number
  remark?: string | null
  expire_mode: 'permanent' | 'custom'
  expire_at?: string | null
  use_mode: 'unlimited' | 'limited'
  max_uses?: number | null
  is_single_use: boolean
}

export type OrderStatus = 'pending' | 'shipped' | 'completed' | 'cancelled'

export interface OrderItem {
  id: number
  product_id?: number | null
  variant_id?: number | null
  product_name: string
  /** 下单时的规格快照，规格后续被删除也仍可追溯 */
  variant_name?: string | null
  price: number
  quantity: number
  subtotal: number
}

export interface Order {
  id: number
  order_no: string
  link_id?: number | null
  link_remark?: string | null
  customer_name: string
  customer_phone: string
  customer_address: string
  remark?: string | null
  total_amount: number
  status: OrderStatus
  status_label: string
  item_count: number
  created_at?: string | null
  updated_at?: string | null
  items: OrderItem[]
}

export interface OrderQuery {
  keyword?: string
  link_id?: number
  status?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}
