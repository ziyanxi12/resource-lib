import { getUserInfo, type UserInfo } from './auth'
import { api } from '../api'

export async function checkAuth(): Promise<{
  status: 'ok' | 'redirect' | 'denied'
  user?: UserInfo
}> {
  const user = getUserInfo()
  if (!user) return { status: 'redirect' }
  const r = await api.checkWhitelist(user.account)
  if (!r.allowed) return { status: 'denied', user }
  return { status: 'ok', user }
}