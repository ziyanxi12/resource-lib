import { getUserInfo, type UserInfo } from './auth'

const WHITELIST_URL = `${import.meta.env.BASE_URL}whitelist.json`
let cachedWhitelist: Set<string> | null = null

export async function loadWhitelist(): Promise<Set<string>> {
  if (cachedWhitelist) return cachedWhitelist
  const res = await fetch(WHITELIST_URL)
  if (!res.ok) throw new Error(`加载白名单失败: HTTP ${res.status}`)
  const accounts: string[] = await res.json()
  cachedWhitelist = new Set(accounts)
  return cachedWhitelist
}

export function isWhitelisted(user: UserInfo, whitelist: Set<string>): boolean {
  return whitelist.has(user.account)
}

export async function checkAuth(): Promise<{
  status: 'ok' | 'redirect' | 'denied'
  user?: UserInfo
}> {
  const user = getUserInfo()
  if (!user) return { status: 'redirect' }
  const whitelist = await loadWhitelist()
  if (!isWhitelisted(user, whitelist)) return { status: 'denied', user }
  return { status: 'ok', user }
}
