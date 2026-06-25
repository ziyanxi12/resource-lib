import { useState } from 'react'
import { ConfigProvider } from 'antd'
import {
  AppstoreOutlined,
  BlockOutlined,
  FileTextOutlined,
  PictureOutlined,
  StarOutlined,
  FunctionOutlined,
} from '@ant-design/icons'
import ResourceOverview from './pages/ResourceOverview'
import ComponentManage from './pages/ComponentManage'
import TemplateManage from './pages/TemplateManage'
import SVGManage from './pages/SVGManage'
import IllustrationManage from './pages/IllustrationManage'
import ImageManage from './pages/ImageManage'

type PageKey = 'overview' | 'component' | 'template' | 'svg' | 'illustration' | 'image'

const PAGES: Record<PageKey, React.ReactNode> = {
  overview: <ResourceOverview />,
  component: <ComponentManage />,
  template: <TemplateManage />,
  svg: <SVGManage />,
  illustration: <IllustrationManage />,
  image: <ImageManage />,
}

const NAV = [
  { key: 'overview' as PageKey, icon: <AppstoreOutlined />, label: '资源总览' },
  { key: 'component' as PageKey, icon: <BlockOutlined />, label: '组件集' },
  { key: 'template' as PageKey, icon: <FileTextOutlined />, label: '模版' },
  { key: 'svg' as PageKey, icon: <FunctionOutlined />, label: 'SVG 图标' },
  { key: 'illustration' as PageKey, icon: <StarOutlined />, label: '插画' },
  { key: 'image' as PageKey, icon: <PictureOutlined />, label: '图片' },
]

function NavItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 14px',
        margin: '1px 8px',
        borderRadius: 7,
        cursor: 'pointer',
        color: active ? '#fff' : '#94a3b8',
        background: active ? 'rgba(99,102,241,0.25)' : 'transparent',
        fontSize: 14,
        fontWeight: active ? 600 : 400,
        transition: 'all 0.15s',
        userSelect: 'none',
      }}
      onMouseEnter={e => {
        if (!active) {
          e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
          e.currentTarget.style.color = '#e2e8f0'
        }
      }}
      onMouseLeave={e => {
        if (!active) {
          e.currentTarget.style.background = 'transparent'
          e.currentTarget.style.color = '#94a3b8'
        }
      }}
    >
      <span style={{ fontSize: 15, display: 'flex', opacity: active ? 1 : 0.7 }}>{icon}</span>
      {label}
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState<PageKey>('overview')

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#6366f1',
          borderRadius: 8,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', 'PingFang SC', sans-serif",
          colorBgContainer: '#ffffff',
          boxShadow: '0 1px 3px 0 rgba(0,0,0,0.07), 0 1px 2px -1px rgba(0,0,0,0.07)',
        },
        components: {
          Table: { headerBg: '#f8fafc', borderColor: '#f1f5f9' },
          Input: { activeShadow: '0 0 0 3px rgba(99,102,241,0.12)' },
          Button: { primaryShadow: '0 1px 3px rgba(99,102,241,0.4)' },
        },
      }}
    >
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        {/* ── Sidebar ── */}
        <aside
          style={{
            width: 216,
            background: '#0f172a',
            position: 'fixed',
            inset: '0 auto 0 0',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 100,
          }}
        >
          {/* Logo */}
          <div
            style={{
              padding: '18px 20px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 8,
                background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 800,
                fontSize: 15,
                flexShrink: 0,
                letterSpacing: -0.5,
              }}
            >
              R
            </div>
            <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 600, letterSpacing: -0.2 }}>
              资源库管理
            </span>
          </div>

          {/* Nav */}
          <nav style={{ flex: 1, padding: '10px 0', overflowY: 'auto' }}>
            <div style={{ padding: '6px 16px 4px', fontSize: 11, color: '#475569', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              导航
            </div>
            {NAV.map(item => (
              <NavItem
                key={item.key}
                icon={item.icon}
                label={item.label}
                active={page === item.key}
                onClick={() => setPage(item.key)}
              />
            ))}
          </nav>

          <div style={{ padding: '14px 20px', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: 11, color: '#334155' }}>
            v0.1.0 · mock 模式
          </div>
        </aside>

        {/* ── Content ── */}
        <main
          style={{
            flex: 1,
            marginLeft: 216,
            minHeight: '100vh',
            background: '#f1f5f9',
            padding: '28px 32px',
          }}
        >
          {PAGES[page]}
        </main>
      </div>
    </ConfigProvider>
  )
}
