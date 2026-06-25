import { useState, useEffect, useCallback } from 'react'
import { Button, Alert, Table, Tag, Space, Statistic, Typography, Popconfirm, message } from 'antd'
import { SyncOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api } from '../api'
import type { Resource, SyncResult } from '../types'

const COLORS = ['#f59e0b', '#f97316', '#ef4444', '#ec4899', '#8b5cf6', '#6366f1']
function pickColor(str: string) {
  let h = 0; for (const c of str) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  return COLORS[h % COLORS.length]
}

export default function IllustrationManage() {
  const [syncing, setSyncing]       = useState(false)
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null)
  const [syncError, setSyncError]   = useState<string | null>(null)
  const [items, setItems]           = useState<Resource[]>([])
  const [total, setTotal]           = useState(0)
  const [page, setPage]             = useState(1)
  const [loading, setLoading]       = useState(false)

  const fetchItems = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listResources({ type: 'illustration', page, limit: 20 })
      setItems(data.items); setTotal(data.total)
    } catch { message.error('加载插画列表失败') }
    finally { setLoading(false) }
  }, [page])

  useEffect(() => { fetchItems() }, [fetchItems])

  const handleSync = async () => {
    setSyncing(true); setSyncResult(null); setSyncError(null)
    try {
      const r: SyncResult = await api.syncIcon('illustration')
      setSyncResult(r)
      if (page === 1) fetchItems(); else setPage(1)
    } catch (e) { setSyncError(e instanceof Error ? e.message : String(e)) }
    finally { setSyncing(false) }
  }

  const handleDelete = async (id: number) => {
    try { await api.deleteResource(id); message.success('已删除'); fetchItems() }
    catch { message.error('删除失败') }
  }

  const columns: ColumnsType<Resource> = [
    {
      title: '插画名称',
      dataIndex: 'name',
      render: (name: string, r) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 9,
            background: pickColor(r.english_name ?? name) + '18',
            border: `1.5px solid ${pickColor(r.english_name ?? name)}30`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13, fontWeight: 700, color: pickColor(r.english_name ?? name),
            fontFamily: 'ui-monospace, monospace', flexShrink: 0,
          }}>
            {(r.english_name ?? name).slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 500, color: '#0f172a' }}>{name}</div>
            {r.english_name && <div style={{ fontSize: 12, color: '#94a3b8', fontFamily: 'ui-monospace, monospace' }}>{r.english_name}</div>}
          </div>
        </div>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string | null) => v ?? <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 160,
      render: (tags: string[]) =>
        tags.length
          ? <Space size={4} wrap>{tags.map(t => <Tag key={t} style={{ margin: 0, borderRadius: 4 }}>{t}</Tag>)}</Space>
          : <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '',
      width: 60, align: 'right' as const,
      render: (_: unknown, r: Resource) => (
        <Popconfirm title="确认删除？" okText="删除" okButtonProps={{ danger: true }} onConfirm={() => handleDelete(r.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>插画</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>共 {total} 条插画数据</p>
      </div>

      <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
        {/* Toolbar */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button type="primary" icon={<SyncOutlined spin={syncing} />} loading={syncing} onClick={handleSync}>
            同步插画数据
          </Button>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            从外部 API 拉取最新数据并写入数据库
          </Typography.Text>
        </div>

        {syncResult && (
          <div style={{ padding: '12px 20px', borderBottom: '1px solid #f1f5f9', background: '#f0fdf4' }}>
            <Space size={40}>
              <Statistic title={<span style={{ fontSize: 12 }}>新增</span>} value={syncResult.added} valueStyle={{ fontSize: 20, color: '#059669', fontWeight: 700 }} />
              <Statistic title={<span style={{ fontSize: 12 }}>更新</span>} value={syncResult.updated} valueStyle={{ fontSize: 20, color: '#6366f1', fontWeight: 700 }} />
              <span style={{ fontSize: 13, color: '#059669' }}>{syncResult.message}</span>
            </Space>
          </div>
        )}
        {syncError && (
          <Alert style={{ borderRadius: 0, margin: 0 }} message="同步失败" description={syncError} type="error" showIcon />
        )}

        <Table
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={loading}
          size="middle"
          style={{ borderRadius: 0 }}
          pagination={{
            current: page, pageSize: 20, total,
            onChange: setPage, showSizeChanger: false,
            showTotal: t => `共 ${t} 条`,
            style: { padding: '12px 20px' },
          }}
          locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无插画数据，点击「同步」获取</div> }}
        />
      </div>
    </div>
  )
}
