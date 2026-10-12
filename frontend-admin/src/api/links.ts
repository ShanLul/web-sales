import { request } from './client'
import type { LinkCreatePayload, PageResult, TempLink } from './types'

export interface LinkQuery {
  keyword?: string
  derived_status?: string
  template_id?: number
  page?: number
  page_size?: number
}

export function listLinks(params: LinkQuery) {
  return request<PageResult<TempLink>>({ url: '/admin/temp-links', method: 'get', params })
}

export function createLink(data: LinkCreatePayload) {
  return request<TempLink>({ url: '/admin/temp-links', method: 'post', data })
}

export function updateLinkStatus(id: number, status: 'active' | 'disabled') {
  return request<TempLink>({
    url: `/admin/temp-links/${id}/status`,
    method: 'patch',
    data: { status },
  })
}

export function voidLink(id: number) {
  return request<TempLink>({ url: `/admin/temp-links/${id}/void`, method: 'post' })
}
