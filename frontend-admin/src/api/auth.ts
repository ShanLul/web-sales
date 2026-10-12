import { request } from './client'
import type { AdminInfo, LoginResult } from './types'

export function login(username: string, password: string) {
  return request<LoginResult>({ url: '/admin/auth/login', method: 'post', data: { username, password } })
}

export function fetchProfile() {
  return request<AdminInfo>({ url: '/admin/auth/profile', method: 'get' })
}
