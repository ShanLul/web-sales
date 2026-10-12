import { request } from './client'
import type { CatalogResult, OrderCreated } from './types'

export function fetchCatalog(token: string, params?: { category_id?: number; keyword?: string }) {
  return request<CatalogResult>({
    url: '/portal/catalog',
    method: 'get',
    params: { t: token, ...params },
  })
}

export interface SubmitOrderPayload {
  token: string
  customer_name: string
  customer_phone: string
  customer_address: string
  remark?: string | null
  items: { product_id: number; variant_id?: number | null; quantity: number }[]
}

export function submitOrder(payload: SubmitOrderPayload) {
  return request<OrderCreated>({ url: '/portal/orders', method: 'post', data: payload })
}
