/** 与后端子系统接口对齐的类型定义。 */

export interface ApiResult<T = unknown> {
  code: number
  message: string
  data: T | null
}

/** 商品规格：单维度互斥可选，价格随规格变化。 */
export interface CatalogVariant {
  id: number
  name: string
  price: number
  image_url?: string | null
}

export interface CatalogProduct {
  id: number
  name: string
  /** 多规格商品后端下发的是起价，实际单价以选中规格为准 */
  price: number
  unit: string
  image_url?: string | null
  description?: string | null
  category_id?: number | null
  category_name?: string | null
  variants?: CatalogVariant[]
}

export interface CatalogCategory {
  id: number
  name: string
}

export interface LinkInfo {
  remark?: string | null
  expire_at?: string | null
  remaining_uses?: number | null
  is_single_use: boolean
  template_name?: string | null
}

export interface CatalogResult {
  link: LinkInfo
  categories: CatalogCategory[]
  products: CatalogProduct[]
}

export interface OrderCreated {
  order_no: string
  total_amount: number
  created_at?: string | null
}

export interface CartLine {
  /** 购物车条目标识：`商品id:规格id`，无规格时为 `商品id:0` */
  key: string
  product: CatalogProduct
  variant: CatalogVariant | null
  /** 该条目实际单价：有规格取规格价，否则取商品价 */
  price: number
  quantity: number
}

/** 链接失效原因码，与后端 ErrorCode / LINK_REASON_MAP 对应。 */
export type FailureReason =
  | 'LINK_NOT_FOUND'
  | 'LINK_EXPIRED'
  | 'LINK_EXHAUSTED'
  | 'LINK_DISABLED'
  | 'LINK_VOIDED'
  | 'UNKNOWN'
