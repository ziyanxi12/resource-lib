import { useState, useEffect, useCallback } from 'react'
import { Button, Alert, Space, Statistic, Typography, Popconfirm, message, Input, Spin } from 'antd'
import { SyncOutlined, DeleteOutlined } from '@ant-design/icons'
import { api } from '../api'
import type { Resource, SyncResult } from '../types'

const GRADIENTS = [
  ['#6366f1', '#8b5cf6'],
  ['#06b6d4', '#3b82f6'],
  ['#10b981', '#059669'],
  ['#f59e0b', '#ef4444'],
  ['#ec4899', '#8b5cf6'],
  ['#14b8a6', '#06b6d4'],
  ['#f97316', '#f59e0b'],
  ['#8b5cf6', '#ec4899'],
]

function pickGradient(str: string) {
  let h = 0
  for (const c of str) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  return GRADIENTS[h % GRADIENTS.length]
}

interface CardProps {
  item: Resource
  onDelete: (id: number) => void
}

function IconCard({ item, onDelete }: CardProps) {
  const [hovered, setHovered] = useState(false)
  const [g0, g1] = pickGradient(item.english_name ?? item.name)
  const label = (item.english_name ?? item.name).toLowerCase()

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: 'relative',
        background: '#fff',
        borderRadius: 12,
        border: `1px solid ${hovered ? '#c7d2fe' : '#e2e8f0'}`,
        padding: '16px 10px 12px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 10,
        cursor: 'default',
        transition: 'all 0.18s ease',
        transform: hovered ? 'translateY(-2px)' : 'none',
        boxShadow: hovered
          ? '0 8px 24px rgba(99,102,241,0.12)'
          : '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      {/* delete btn */}
      <Popconfirm
        title="确认删除？"
        okText="删除" okButtonProps={{ danger: true }}
        onConfirm={() => onDelete(item.id)}
      >
        <div
          style={{
            position: 'absolute',
            top: 6,
            right: 6,
            opacity: hovered ? 1 : 0,
            transition: 'opacity 0.15s',
          }}
        >
          <Button
            size="small"
            type="text"
            danger
            icon={<DeleteOutlined style={{ fontSize: 11 }} />}
            style={{ width: 22, height: 22, padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          />
        </div>
      </Popconfirm>

      {/* Icon box */}
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 14,
          background: `linear-gradient(135deg, ${g0}, ${g1})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 4px 12px ${g0}50`,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            color: '#fff',
            fontSize: label.length <= 4 ? 14 : label.length <= 6 ? 11 : 9,
            fontWeight: 700,
            fontFamily: 'ui-monospace, SFMono-Regular, monospace',
            letterSpacing: -0.3,
            textAlign: 'center',
            lineHeight: 1.2,
            padding: '0 4px',
            wordBreak: 'break-all',
          }}
        >
          {label.slice(0, 8)}
        </span>
      </div>

      {/* Labels */}
      <div style={{ textAlign: 'center', width: '100%', padding: '0 2px' }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: '#0f172a',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {item.name}
        </div>
        {item.english_name && (
          <div
            style={{
              fontSize: 11,
              color: '#94a3b8',
              marginTop: 1,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              fontFamily: 'ui-monospace, monospace',
            }}
          >
            {item.english_name}
          </div>
        )}
      </div>
    </div>
  )
}

export default function SVGManage() {
  const [syncing, setSyncing]       = useState(false)
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null)
  const [syncError, setSyncError]   = useState<string | null>(null)
  const [allItems, setAllItems]     = useState<Resource[]>([])
  const [keyword, setKeyword]       = useState('')
  const [loading, setLoading]       = useState(false)
  const [total, setTotal]           = useState(0)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listResources({ type: 'svg', limit: 100 })
      setAllItems(data.items)
      setTotal(data.total)
    } catch { message.error('加载失败') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  const handleSync = async () => {
    setSyncing(true); setSyncResult(null); setSyncError(null)
    try {
      const r: SyncResult = await api.syncIcon('svg')
      setSyncResult(r); fetchAll()
    } catch (e) { setSyncError(e instanceof Error ? e.message : String(e)) }
    finally { setSyncing(false) }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.deleteResource(id)
      message.success('已删除')
      setAllItems(p => p.filter(i => i.id !== id))
      setTotal(p => p - 1)
    } catch { message.error('删除失败') }
  }

  const filtered = keyword
    ? allItems.filter(i =>
        i.name.includes(keyword) ||
        (i.english_name ?? '').toLowerCase().includes(keyword.toLowerCase()),
      )
    : allItems

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>SVG 图标</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
          共 {total} 个图标
        </p>
      </div>

      {/* Toolbar */}
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          padding: '14px 18px',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          flexWrap: 'wrap',
        }}
      >
        <Button
          type="primary"
          icon={<SyncOutlined spin={syncing} />}
          loading={syncing}
          onClick={handleSync}
        >
          同步图标数据
        </Button>
        <Input.Search
          placeholder="搜索名称 / 英文名"
          allowClear
          style={{ width: 240 }}
          onSearch={setKeyword}
          onChange={e => { if (!e.target.value) setKeyword('') }}
        />
        {keyword && (
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            找到 {filtered.length} 个结果
          </Typography.Text>
        )}
      </div>

      {syncResult && (
        <Alert
          style={{ marginBottom: 16, borderRadius: 10 }}
          message={syncResult.message}
          type="success" showIcon
          description={
            <Space size={32} style={{ marginTop: 8 }}>
              <Statistic title="新增" value={syncResult.added} valueStyle={{ color: '#059669', fontSize: 18 }} />
              <Statistic title="更新" value={syncResult.updated} valueStyle={{ color: '#6366f1', fontSize: 18 }} />
            </Space>
          }
        />
      )}
      {syncError && (
        <Alert style={{ marginBottom: 16, borderRadius: 10 }} message="同步失败" description={syncError} type="error" showIcon />
      )}

      {/* Icon grid */}
      {loading ? (
        <div style={{ textAlign: 'center', paddingTop: 80 }}><Spin size="large" /></div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 0', color: '#94a3b8' }}>
          {keyword ? `未找到与 "${keyword}" 匹配的图标` : '暂无图标数据，点击「同步」获取'}
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
            gap: 10,
          }}
        >
          {filtered.map(item => (
            <IconCard key={item.id} item={item} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  )
}
