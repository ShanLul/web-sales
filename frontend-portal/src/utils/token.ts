/** 链接 token 在会话内共享：刷新页面后仍能凭同一 token 继续下单。 */
export const TOKEN_KEY = 'web-sales-portal-token'

export function readToken(): string {
  return sessionStorage.getItem(TOKEN_KEY) || ''
}

export function saveToken(token: string): void {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token)
  }
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}
