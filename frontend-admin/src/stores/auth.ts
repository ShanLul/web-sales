/** 管理员登录态：token 持久化到 localStorage，刷新后自动恢复。 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { fetchProfile, login as loginApi } from '../api/auth'
import { TOKEN_KEY } from '../api/client'
import type { AdminInfo } from '../api/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const admin = ref<AdminInfo | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => Boolean(token.value))
  const displayName = computed(() => admin.value?.name || admin.value?.username || '未登录')
  const initial = computed(() => displayName.value.slice(0, 1))

  function setToken(value: string) {
    token.value = value
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const result = await loginApi(username, password)
      setToken(result.token)
      admin.value = result.admin
      return result.admin
    } finally {
      loading.value = false
    }
  }

  /** 刷新页面后凭 token 拉回管理员信息；失败即视为登录失效。 */
  async function restore() {
    if (!token.value) return false
    try {
      admin.value = await fetchProfile()
      return true
    } catch (error) {
      console.error('恢复登录态失败', error)
      logout()
      return false
    }
  }

  function logout() {
    setToken('')
    admin.value = null
  }

  return { token, admin, loading, isLoggedIn, displayName, initial, login, restore, logout }
})
