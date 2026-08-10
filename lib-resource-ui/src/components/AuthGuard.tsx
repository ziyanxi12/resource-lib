import { useEffect, useState } from 'react'
import { checkAuth } from '../utils/whitelist'
import { redirectToLogin, logout, type UserInfo } from '../utils/auth'

type AuthState = 'loading' | 'ok' | 'redirect' | 'denied' | 'error'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>('loading')
  const [user, setUser] = useState<UserInfo | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    checkAuth()
      .then(r => {
        setState(r.status)
        setUser(r.user ?? null)
        if (r.status === 'redirect') redirectToLogin()
      })
      .catch(e => {
        setError(e instanceof Error ? e.message : String(e))
        setState('error')
      })
  }, [])

  if (state === 'loading') return <FullScreenTip text="正在验证登录状态…" />
  if (state === 'redirect') return <FullScreenTip text="正在跳转登录页…" />
  if (state === 'error') return <FullScreenTip text={`登录状态校验失败：${error}`} />
  if (state === 'denied') return <AccessDenied user={user} onLogout={logout} />
  return <>{children}</>
}

function FullScreenTip({ text }: { text: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#f1f5f9',
        fontSize: 15,
        color: '#64748b',
      }}
    >
      {text}
    </div>
  )
}

function AccessDenied({ user, onLogout }: { user: UserInfo | null; onLogout: () => void }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#f1f5f9',
        gap: 16,
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 14,
          background: 'linear-gradient(135deg,#ef4444,#f97316)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 800,
          fontSize: 22,
        }}
      >
        403
      </div>
      <div style={{ fontSize: 18, fontWeight: 600, color: '#1e293b' }}>无权限访问</div>
      <div style={{ fontSize: 14, color: '#64748b', textAlign: 'center' }}>
        您的账号（{user?.nickName ?? '未知'} / {user?.account ?? '未知'}）无权限访问资源库管理系统
      </div>
      <button
        onClick={onLogout}
        style={{
          marginTop: 8,
          padding: '8px 24px',
          borderRadius: 8,
          border: 'none',
          background: '#6366f1',
          color: '#fff',
          fontSize: 14,
          fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        重新登录
      </button>
    </div>
  )
}
