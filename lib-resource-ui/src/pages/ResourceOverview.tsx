import { useState, useEffect } from 'react'
import {
  BlockOutlined, FileTextOutlined, FunctionOutlined, StarOutlined, PictureOutlined,
} from '@ant-design/icons'
import { api } from '../api'

const STATS = [
  { key: 'component_set', label: '组件',  icon: <BlockOutlined />,    color: '#6366f1', bg: '#eef2ff' },
  { key: 'template',      label: '模版',  icon: <FileTextOutlined />, color: '#7c3aed', bg: '#f5f3ff' },
  { key: 'svg',           label: '图标',  icon: <FunctionOutlined />, color: '#0891b2', bg: '#ecfeff' },
  { key: 'illustration',  label: '插画',  icon: <StarOutlined />,     color: '#d97706', bg: '#fffbeb' },
  { key: 'image',         label: '图片',  icon: <PictureOutlined />,  color: '#059669', bg: '#ecfdf5' },
]

function StatCard({
  label, icon, color, bg, count,
}: {
  label: string; icon: React.ReactNode; color: string; bg: string; count: number | null
}) {
  const [hov, setHov] = useState(false)
  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? bg : '#fff',
        borderRadius: 14,
        border: `1.5px solid ${hov ? color : '#e2e8f0'}`,
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        flex: 1,
        minWidth: 160,
        cursor: 'default',
        transition: 'all 0.18s ease',
        boxShadow: hov ? `0 4px 20px ${color}22` : '0 1px 3px rgba(0,0,0,0.04)',
        transform: hov ? 'translateY(-2px)' : 'none',
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 13,
          background: hov ? color : bg,
          color: hov ? '#fff' : color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          flexShrink: 0,
          transition: 'all 0.18s',
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 800, color: hov ? color : '#0f172a', lineHeight: 1.1, transition: 'color 0.18s' }}>
          {count ?? '—'}
        </div>
        <div style={{ fontSize: 14, color: hov ? color : '#64748b', marginTop: 4, fontWeight: hov ? 600 : 400 }}>
          {label}
        </div>
      </div>
    </div>
  )
}

export default function ResourceOverview() {
  const [counts, setCounts] = useState<Record<string, number>>({})

  useEffect(() => {
    Promise.all(
      STATS.map(s =>
        api.listResources({ type: s.key, limit: 1 })
          .then(d => ({ key: s.key, total: d.total as number }))
          .catch(() => ({ key: s.key, total: 0 }))
      )
    ).then(results => {
      const m: Record<string, number> = {}
      results.forEach(r => { m[r.key] = r.total })
      setCounts(m)
    })
  }, [])

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>数据总览</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>五类设计资源的当前数量</p>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {STATS.map(s => (
          <StatCard
            key={s.key}
            label={s.label}
            icon={s.icon}
            color={s.color}
            bg={s.bg}
            count={counts[s.key] ?? null}
          />
        ))}
      </div>
    </div>
  )
}
