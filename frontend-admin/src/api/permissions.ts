import { request } from './client'
import type { PageResult, PermissionTemplate, ProductBrief, TemplateOption } from './types'

export function listTemplates(params: { keyword?: string; page?: number; page_size?: number }) {
  return request<PageResult<PermissionTemplate>>({
    url: '/admin/permission-templates',
    method: 'get',
    params,
  })
}

export function listTemplateOptions() {
  return request<TemplateOption[]>({ url: '/admin/permission-templates/options', method: 'get' })
}

export function getTemplate(id: number) {
  return request<PermissionTemplate>({ url: `/admin/permission-templates/${id}`, method: 'get' })
}

export function getTemplateProducts(id: number) {
  return request<ProductBrief[]>({ url: `/admin/permission-templates/${id}/products`, method: 'get' })
}

export function createTemplate(data: {
  name: string
  description?: string | null
  is_active: boolean
  product_ids: number[]
}) {
  return request<PermissionTemplate>({ url: '/admin/permission-templates', method: 'post', data })
}

export function updateTemplate(
  id: number,
  data: {
    name?: string
    description?: string | null
    is_active?: boolean
    product_ids?: number[]
  },
) {
  return request<PermissionTemplate>({ url: `/admin/permission-templates/${id}`, method: 'put', data })
}

export function duplicateTemplate(id: number, name: string) {
  return request<PermissionTemplate>({
    url: `/admin/permission-templates/${id}/duplicate`,
    method: 'post',
    data: { name },
  })
}

export function deleteTemplate(id: number) {
  return request<{ id: number }>({ url: `/admin/permission-templates/${id}`, method: 'delete' })
}
