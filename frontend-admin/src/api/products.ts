import { request } from './client'
import type {
  Category,
  PageResult,
  Product,
  ProductStatus,
  ProductVariantInput,
} from './types'

export interface ProductQuery {
  keyword?: string
  category_id?: number
  status?: string
  page?: number
  page_size?: number
}

/** 商品入参：variants 为整体替换，传空数组即清空规格。 */
export interface ProductPayload {
  name: string
  sku?: string | null
  category_id?: number | null
  price: number
  unit: string
  image_url?: string | null
  description?: string | null
  status: ProductStatus
  variants?: ProductVariantInput[]
}

export function listProducts(params: ProductQuery) {
  return request<PageResult<Product>>({ url: '/admin/products', method: 'get', params })
}

export function createProduct(data: ProductPayload) {
  return request<Product>({ url: '/admin/products', method: 'post', data })
}

export function updateProduct(id: number, data: Partial<ProductPayload>) {
  return request<Product>({ url: `/admin/products/${id}`, method: 'put', data })
}

export function updateProductStatus(id: number, status: ProductStatus) {
  return request<Product>({ url: `/admin/products/${id}/status`, method: 'patch', data: { status } })
}

export function deleteProduct(id: number) {
  return request<{ id: number }>({ url: `/admin/products/${id}`, method: 'delete' })
}

export function listCategories() {
  return request<Category[]>({ url: '/admin/categories', method: 'get' })
}

export function createCategory(data: { name: string; sort_order: number }) {
  return request<Category>({ url: '/admin/categories', method: 'post', data })
}

export function updateCategory(id: number, data: { name?: string; sort_order?: number }) {
  return request<Category>({ url: `/admin/categories/${id}`, method: 'put', data })
}

export function deleteCategory(id: number) {
  return request<{ id: number }>({ url: `/admin/categories/${id}`, method: 'delete' })
}
