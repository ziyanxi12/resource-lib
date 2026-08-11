const STORAGE_KEYS = [
  'account', 'dept', 'deptCode', 'nickName',
  'roleID', 'roles', 'uid', 'userID',
] as const

export interface UserInfo {
  account: string
  dept: string[]
  deptCode: string[]
  nickName: string
  roleID: string
  roles: string[]
  uid: number
  userID: string
}

export function getUserInfo(): UserInfo | null {
  const account = localStorage.getItem('account')
  const nickName = localStorage.getItem('nickName')
  if (!account || !nickName) return null
  try {
    const uid = Number(localStorage.getItem('uid'))
    if (!Number.isFinite(uid)) return null
    return {
      account,
      nickName,
      dept: JSON.parse(localStorage.getItem('dept') ?? '[]'),
      deptCode: JSON.parse(localStorage.getItem('deptCode') ?? '[]'),
      roleID: localStorage.getItem('roleID') ?? '',
      roles: JSON.parse(localStorage.getItem('roles') ?? '[]'),
      uid,
      userID: localStorage.getItem('userID') ?? '',
    }
  } catch {
    return null
  }
}

export function isLoggedIn(): boolean {
  return getUserInfo() !== null
}

export async function getEncryptedUserData(): Promise<string> {
  const user = getUserInfo()
  if (!user) return ''
  const { encryptUserData } = await import('./crypto')
  return encryptUserData({ ...user })
}

export function redirectToLogin(): void {
  const redirect = window.location.href
  localStorage.setItem('login_redirect', redirect)
  window.location.href =
    '/signIn/index.html?model=web&redirect=' +
    encodeURIComponent(redirect)
}

export function logout(): void {
  STORAGE_KEYS.forEach(key => localStorage.removeItem(key))
  redirectToLogin()
}
