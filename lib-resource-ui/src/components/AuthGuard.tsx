import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { checkAuth } from '../utils/whitelist'
import { redirectToLogin, type UserInfo } from '../utils/auth'

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
      .catch((e: any) => {
        setError(e?.message ? String(e.message) : String(e))
        setState('error')
      })
  }, [])

  if (state === 'loading') return <FullScreenTip text="正在验证登录状态…" />
  if (state === 'redirect') return <FullScreenTip text="正在跳转登录页…" />
  if (state === 'error') return <FullScreenTip text={`登录状态校验失败：${error}`} />
  if (state === 'denied') return <Navigate to="/error" replace />
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
