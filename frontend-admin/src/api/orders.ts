import { download, request } from './client'
import type { Order, OrderQuery, OrderStatus, PageResult } from './types'

export function listOrders(params: OrderQuery) {
  return request<PageResult<Order>>({ url: '/admin/orders', method: 'get', params })
}

export function getOrder(id: number) {
  return request<Order>({ url: `/admin/orders/${id}`, method: 'get' })
}

export function updateOrderStatus(id: number, status: OrderStatus) {
  return request<Order>({ url: `/admin/orders/${id}/status`, method: 'patch', data: { status } })
}

export function exportOrders(params: Omit<OrderQuery, 'page' | 'page_size'>) {
  return download('/admin/exports/orders', params)
}

export function exportProducts(params: { keyword?: string; category_id?: number; status?: string }) {
  return download('/admin/exports/products', params)
}
