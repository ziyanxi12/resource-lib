import { getUserInfo, type UserInfo } from './auth'
import { api } from '../api'

export type Role = 'super' | 'admin' | null

export async function checkAuth(): Promise<{
  status: 'ok' | 'redirect' | 'denied'
  user?: UserInfo
  role?: Role
}> {
  const user = getUserInfo()
  if (!user) return { status: 'redirect' }
  const r = await api.checkWhitelist(user.account)
  if (!r.allowed) return { status: 'denied', user }
  const role: Role = r.role === 'super' ? 'super' : r.role === 'admin' ? 'admin' : null
  return { status: 'ok', user, role }
}