import { useState } from 'react'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import {
  AppstoreOutlined,
  BlockOutlined,
  FileTextOutlined,
  PictureOutlined,
  StarOutlined,
  FunctionOutlined,
  FileOutlined,
} from '@ant-design/icons'
import ResourceOverview from './pages/ResourceOverview'
import ComponentManage from './pages/ComponentManage'
import TemplateManage from './pages/TemplateManage'
import SVGManage from './pages/SVGManage'
import IllustrationManage from './pages/IllustrationManage'
import ImageManage from './pages/ImageManage'
import FileManage from './pages/FileManage'

type PageKey = 'overview' | 'component' | 'template' | 'icon' | 'illus' | 'image' | 'file'

const PAGES: Record<PageKey, React.ReactNode> = {
  overview:  <ResourceOverview />,
  component: <ComponentManage />,
  template:  <TemplateManage />,
  icon:      <SVGManage />,
  illus:     <IllustrationManage />,
  image:     <ImageManage />,
  file:      <FileManage />,
}

const NAV = [
  { key: 'overview'  as PageKey, icon: <AppstoreOutlined />,  label: '数据总览' },
  { key: 'component' as PageKey, icon: <BlockOutlined />,     label: '组件' },
  { key: 'template'  as PageKey, icon: <FileTextOutlined />,  label: '模版' },
  { key: 'icon'      as PageKey, icon: <FunctionOutlined />,  label: '图标' },
  { key: 'illus'     as PageKey, icon: <StarOutlined />,      label: '插画' },
  { key: 'image'     as PageKey, icon: <PictureOutlined />,   label: '图片' },
  { key: 'file'      as PageKey, icon: <FileOutlined />,      label: '文件' },
]

const HEADER_H = 56
const SIDEBAR_W = 200

function NavItem({
  icon, label, active, onClick,
}: {
  icon: React.ReactNode; label: string; active: boolean; onClick: () => void
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
      locale={zhCN}
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
      {/* ── Top header ── */}
      <header
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: HEADER_H,
          background: '#fff',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          zIndex: 200,
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 800,
              fontSize: 16,
              flexShrink: 0,
            }}
          >
            R
          </div>
          <span style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', letterSpacing: -0.3 }}>
            资源库管理
          </span>
        </div>
      </header>

      <div style={{ display: 'flex', minHeight: '100vh', paddingTop: HEADER_H }}>
        {/* ── Sidebar ── */}
        <aside
          style={{
            width: SIDEBAR_W,
            background: '#0f172a',
            position: 'fixed',
            top: HEADER_H,
            left: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            zIndex: 100,
          }}
        >
          <nav style={{ flex: 1, padding: '12px 0', overflowY: 'auto' }}>
            <div
              style={{
                padding: '6px 16px 8px',
                fontSize: 11,
                color: '#475569',
                fontWeight: 600,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
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

          <div
            style={{
              padding: '14px 20px',
              borderTop: '1px solid rgba(255,255,255,0.06)',
              fontSize: 11,
              color: '#334155',
            }}
          >
            v{__APP_VERSION__}
          </div>
        </aside>

        {/* ── Content ── */}
        <main
          style={{
            flex: 1,
            marginLeft: SIDEBAR_W,
            height: `calc(100vh - ${HEADER_H}px)`,
            background: '#f1f5f9',
            padding: '28px 32px',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* inner wrapper so page components can use flex:1 to fill height */}
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            {PAGES[page]}
          </div>
        </main>
      </div>
    </ConfigProvider>
  )
}
