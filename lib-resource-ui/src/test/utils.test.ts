import { describe, it, expect } from 'vitest'
import { getUserInfo, isLoggedIn } from '../utils/auth'

describe('getUserInfo', () => {
  it('正常返回用户信息', () => {
    localStorage.setItem('userInfo', JSON.stringify({
      account: 'admin', nickName: '管理员',
      dept: [], deptCode: [], roleID: '1', roles: [],
      uid: 1, userID: '1',
    }))
    const user = getUserInfo()
    expect(user).not.toBeNull()
    expect(user?.account).toBe('admin')
    expect(user?.nickName).toBe('管理员')
  })

  it('无 localStorage 时返回 null', () => {
    expect(getUserInfo()).toBeNull()
  })

  it('JSON 格式错误时返回 null', () => {
    localStorage.setItem('userInfo', 'not-json')
    expect(getUserInfo()).toBeNull()
  })

  it('缺少 account 时返回 null', () => {
    localStorage.setItem('userInfo', JSON.stringify({ nickName: '管理员' }))
    expect(getUserInfo()).toBeNull()
  })

  it('缺少 nickName 时返回 null', () => {
    localStorage.setItem('userInfo', JSON.stringify({ account: 'admin' }))
    expect(getUserInfo()).toBeNull()
  })
})

describe('isLoggedIn', () => {
  it('有有效用户信息时返回 true', () => {
    localStorage.setItem('userInfo', JSON.stringify({
      account: 'admin', nickName: '管理员',
      dept: [], deptCode: [], roleID: '1', roles: [],
      uid: 1, userID: '1',
    }))
    expect(isLoggedIn()).toBe(true)
  })

  it('无用户信息时返回 false', () => {
    expect(isLoggedIn()).toBe(false)
  })
})
