/** 子系统请求封装：统一解包响应体，并把链接失效原因抛出为可识别的错误。 */
import axios from 'axios'

import type { ApiResult, FailureReason } from './types'

/** 一般业务失败（如商品不在授权范围、提交过于频繁），由调用方就地提示。 */
export class ApiError extends Error {
  code: number

  constructor(message: string, code: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

/** 链接本身不可用，需要整页渲染失效原因。 */
export class LinkError extends ApiError {
  reason: FailureReason

  constructor(message: string, code: number, reason: FailureReason) {
    super(message, code)
    this.name = 'LinkError'
    this.reason = reason
  }
}

export const http = axios.create({
  baseURL: '/api',
  timeout: 20000,
})

/** 链接类错误码 → 失效原因，与后端 LINK_REASON_MAP 保持一致。 */
const REASON_BY_CODE: Record<number, FailureReason> = {
  1001: 'LINK_NOT_FOUND',
  1002: 'LINK_EXPIRED',
  1003: 'LINK_EXHAUSTED',
  1004: 'LINK_DISABLED',
  1005: 'LINK_VOIDED',
}

export async function request<T>(config: Parameters<typeof http.request>[0]): Promise<T> {
  const response = await http.request<ApiResult<T>>(config)
  const body = response.data

  if (body.code !== 0) {
    const message = body.message || '请求失败'
    const reason =
      (body.data as { reason?: FailureReason } | null)?.reason ?? REASON_BY_CODE[body.code]
    if (reason) {
      throw new LinkError(message, body.code, reason)
    }
    throw new ApiError(message, body.code)
  }

  return body.data as T
}
