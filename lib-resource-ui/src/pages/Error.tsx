import { getUserInfo, logout } from '../utils/auth'

export default function Error() {
  const user = getUserInfo()
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
      <div style={{ fontSize: 18, fontWeight: 600, color: '#1e293b' }}>访问受限</div>
      <div style={{ fontSize: 14, color: '#64748b', textAlign: 'center' }}>
        非白名单用户
      </div>
      {user && (
        <div style={{ fontSize: 13, color: '#94a3b8', textAlign: 'center' }}>
          {user.nickName} / {user.account}
        </div>
      )}
      <button
        onClick={() => logout()}
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
