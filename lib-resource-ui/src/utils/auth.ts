const STORAGE_KEYS = [
  'account', 'dept', 'deptcode', 'nickName',
  'roleId', 'roles', 'uid', 'uuid',
] as const

export interface UserInfo {
  account: string
  dept: string[]
  deptcode: string[]
  nickName: string
  roleId: string
  roles: string
  uid: string
  uuid: string
}

export function getUserInfo(): UserInfo | null {
  const account = localStorage.getItem('account')
  const nickName = localStorage.getItem('nickName')
  if (!account || !nickName) return null
  try {
    return {
      account,
      nickName,
      dept: JSON.parse(localStorage.getItem('dept') ?? '[]'),
      deptcode: JSON.parse(localStorage.getItem('deptcode') ?? '[]'),
      roleId: localStorage.getItem('roleId') ?? '',
      roles: localStorage.getItem('roles') ?? '',
      uid: localStorage.getItem('uid') ?? '',
      uuid: localStorage.getItem('uuid') ?? '',
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
  window.location.href =
    '/signIn/index.html?model=web&redirect=' +
    encodeURIComponent(window.location.href)
}

export function logout(): void {
  STORAGE_KEYS.forEach(key => localStorage.removeItem(key))
  redirectToLogin()
}
