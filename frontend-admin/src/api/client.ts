/** axios 实例：统一注入 JWT、统一解包 {code, message, data}、统一错误提示。 */
import axios from 'axios'
import { MessagePlugin } from 'tdesign-vue-next'

import type { ApiResult } from './types'

export const TOKEN_KEY = 'web-sales-admin-token'

export const http = axios.create({
  baseURL: '/api',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** 401 时清理登录态并跳回登录页，避免反复弹出无意义提示。 */
function redirectToLogin() {
  localStorage.removeItem(TOKEN_KEY)
  if (window.location.hash !== '#/login') {
    window.location.hash = '#/login'
  }
}

http.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResult
    // 导出等二进制响应不走统一解包
    if (!body || typeof body.code !== 'number') {
      return response
    }
    if (body.code !== 0) {
      MessagePlugin.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return response
  },
  (error) => {
    const status = error?.response?.status
    const message: string = error?.response?.data?.message || error?.message || '网络异常，请稍后重试'
    if (status === 401) {
      MessagePlugin.warning('登录已失效，请重新登录')
      redirectToLogin()
    } else {
      MessagePlugin.error(message)
    }
    return Promise.reject(error)
  },
)

/** 业务接口统一返回 data 字段，这里做一次解包。 */
export async function request<T>(config: Parameters<typeof http.request>[0]): Promise<T> {
  const response = await http.request<ApiResult<T>>(config)
  return response.data.data as T
}

/** 下载二进制文件（Excel 导出）。 */
export async function download(url: string, params?: Record<string, unknown>): Promise<void> {
  const response = await http.get(url, { params, responseType: 'blob' })
  const blob = response.data as Blob
  const disposition = String(response.headers['content-disposition'] || '')
  const matched = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition)
  const fallback = `导出数据_${Date.now()}.xlsx`
  const filename = matched ? decodeURIComponent(matched[1]) : fallback

  const objectUrl = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  window.URL.revokeObjectURL(objectUrl)
}
