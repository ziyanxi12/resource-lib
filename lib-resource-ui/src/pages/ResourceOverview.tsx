import { useState, useEffect, useCallback } from 'react'
import {
  Table, Tabs, Input, Button, Space, Tag, Modal, Form,
  InputNumber, Select, message, Popconfirm, Typography,
} from 'antd'
import {
  EditOutlined, DeleteOutlined, BlockOutlined, FileTextOutlined,
  FunctionOutlined, StarOutlined, PictureOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api } from '../api'
import type { Resource } from '../types'

// ── stat card config ──────────────────────────────────────────
const STAT_TYPES = [
  { key: 'component_set', label: '组件集', icon: <BlockOutlined />,    color: '#6366f1', bg: '#eef2ff' },
  { key: 'template',      label: '模版',   icon: <FileTextOutlined />, color: '#7c3aed', bg: '#f5f3ff' },
  { key: 'svg',           label: 'SVG',   icon: <FunctionOutlined />, color: '#0891b2', bg: '#ecfeff' },
  { key: 'illustration',  label: '插画',   icon: <StarOutlined />,     color: '#d97706', bg: '#fffbeb' },
  { key: 'image',         label: '图片',   icon: <PictureOutlined />,  color: '#059669', bg: '#ecfdf5' },
]

const TYPE_TABS = [
  { key: '',              label: '全部'  },
  { key: 'component_set', label: '组件集' },
  { key: 'template',      label: '模版'  },
  { key: 'svg',           label: 'SVG'  },
  { key: 'illustration',  label: '插画'  },
  { key: 'image',         label: '图片'  },
]

const TYPE_LABEL: Record<string, string> = {
  component_set: '组件集', template: '模版', svg: 'SVG', illustration: '插画', image: '图片',
}
const TYPE_COLOR: Record<string, string> = {
  component_set: '#6366f1', template: '#7c3aed', svg: '#0891b2', illustration: '#d97706', image: '#059669',
}
const TYPE_BG: Record<string, string> = {
  component_set: '#eef2ff', template: '#f5f3ff', svg: '#ecfeff', illustration: '#fffbeb', image: '#ecfdf5',
}

// ── stat card ─────────────────────────────────────────────────
function StatCard({
  label, icon, color, bg, count, active, onClick,
}: {
  label: string; icon: React.ReactNode; color: string; bg: string
  count: number | null; active: boolean; onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      style={{
        background: active ? bg : '#fff',
        borderRadius: 12,
        border: `1.5px solid ${active ? color : '#e2e8f0'}`,
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        flex: 1,
        minWidth: 0,
        cursor: 'pointer',
        transition: 'all 0.18s ease',
        boxShadow: active ? `0 4px 16px ${color}20` : '0 1px 3px rgba(0,0,0,0.04)',
        transform: active ? 'translateY(-1px)' : 'none',
      }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.borderColor = color + '60' }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.borderColor = '#e2e8f0' }}
    >
      <div
        style={{
          width: 44, height: 44, borderRadius: 10,
          background: active ? color : bg,
          color: active ? '#fff' : color,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, flexShrink: 0,
          transition: 'all 0.18s',
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 700, color: active ? color : '#0f172a', lineHeight: 1.2, transition: 'color 0.18s' }}>
          {count ?? '—'}
        </div>
        <div style={{ fontSize: 13, color: active ? color : '#64748b', marginTop: 2, fontWeight: active ? 600 : 400 }}>{label}</div>
      </div>
    </div>
  )
}

// ── main component ────────────────────────────────────────────
export default function ResourceOverview() {
  const [statCounts, setStatCounts] = useState<Record<string, number>>({})
  const [activeType, setActiveType] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage]   = useState(1)
  const limit = 20
  const [total, setTotal] = useState(0)
  const [items, setItems] = useState<Resource[]>([])
  const [loading, setLoading] = useState(false)

  const [editItem, setEditItem]     = useState<Resource | null>(null)
  const [editForm]                  = Form.useForm()
  const [editLoading, setEditLoading] = useState(false)

  // fetch stat counts once
  useEffect(() => {
    Promise.all(
      STAT_TYPES.map(s =>
        api.listResources({ type: s.key, limit: 1 }).then(d => ({ key: s.key, total: d.total as number }))
      )
    ).then(results => {
      const m: Record<string, number> = {}
      results.forEach(r => { m[r.key] = r.total })
      setStatCounts(m)
    }).catch(() => {})
  }, [])

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listResources({
        type:   activeType || undefined,
        page,
        limit,
        search: search || undefined,
      })
      setItems(data.items)
      setTotal(data.total)
    } catch {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }, [activeType, page, limit, search])

  useEffect(() => { fetchData() }, [fetchData])

  const openEdit = (record: Resource) => {
    setEditItem(record)
    editForm.setFieldsValue({
      name: record.name, description: record.description,
      sort_order: record.sort_order, tags: record.tags,
    })
  }

  const handleEditSubmit = async () => {
    const values = await editForm.validateFields()
    if (!editItem) return
    setEditLoading(true)
    try {
      await api.updateResource(editItem.id, values)
      message.success('更新成功')
      setEditItem(null)
      fetchData()
    } catch { message.error('更新失败') } finally { setEditLoading(false) }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.deleteResource(id)
      message.success('已删除')
      fetchData()
    } catch { message.error('删除失败') }
  }

  const columns: ColumnsType<Resource> = [
    { title: 'ID', dataIndex: 'id', width: 64, render: (v: number) => <span style={{ color: '#94a3b8', fontSize: 12 }}>#{v}</span> },
    {
      title: '名称',
      dataIndex: 'name',
      render: (name: string, r) => (
        <div>
          <div style={{ fontWeight: 500, color: '#0f172a' }}>{name}</div>
          {r.english_name && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 1 }}>{r.english_name}</div>}
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'resource_type_name',
      width: 88,
      render: (v: string) => (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px 10px',
            borderRadius: 20,
            fontSize: 12,
            fontWeight: 500,
            background: TYPE_BG[v] ?? '#f1f5f9',
            color: TYPE_COLOR[v] ?? '#64748b',
          }}
        >
          {TYPE_LABEL[v] ?? v}
        </span>
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
        tags.length ? (
          <Space size={4} wrap>
            {tags.map(t => (
              <Tag key={t} style={{ margin: 0, borderRadius: 4, fontSize: 12 }}>{t}</Tag>
            ))}
          </Space>
        ) : <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 148,
      render: (v: string | null) => (
        <span style={{ fontSize: 12, color: '#94a3b8' }}>
          {v ? v.slice(0, 19).replace('T', ' ') : '—'}
        </span>
      ),
    },
    {
      title: '',
      width: 80,
      align: 'right' as const,
      render: (_: unknown, record: Resource) => (
        <Space size={4}>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            style={{ color: '#6366f1' }}
            onClick={() => openEdit(record)}
          />
          <Popconfirm
            title="确认删除该资源？"
            okText="删除" okButtonProps={{ danger: true }}
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* Page title */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>资源总览</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>管理五类设计资源</p>
      </div>

      {/* Stat cards — click to filter */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        {STAT_TYPES.map(s => (
          <StatCard
            key={s.key}
            label={s.label}
            icon={s.icon}
            color={s.color}
            bg={s.bg}
            count={statCounts[s.key] ?? null}
            active={activeType === s.key}
            onClick={() => {
              const next = activeType === s.key ? '' : s.key
              setActiveType(next)
              setPage(1)
            }}
          />
        ))}
      </div>

      {/* Table card */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {/* Toolbar */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', gap: 12 }}>
          <Tabs
            items={TYPE_TABS.map(t => ({ key: t.key, label: t.label }))}
            activeKey={activeType}
            onChange={k => { setActiveType(k); setPage(1) }}
            size="small"
            style={{ margin: 0 }}
          />
          <div style={{ marginLeft: 'auto' }}>
            <Input.Search
              placeholder="搜索名称 / 英文名 / 描述"
              style={{ width: 280 }}
              allowClear
              onSearch={v => { setSearch(v); setPage(1) }}
            />
          </div>
        </div>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={loading}
          size="middle"
          style={{ borderRadius: 0 }}
          pagination={{
            current: page, pageSize: limit, total,
            onChange: setPage,
            showSizeChanger: false,
            showTotal: t => `共 ${t} 条`,
            style: { padding: '12px 20px' },
          }}
          locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无数据</div> }}
        />
      </div>

      {/* Edit modal */}
      <Modal
        title="编辑资源"
        open={!!editItem}
        onOk={handleEditSubmit}
        onCancel={() => setEditItem(null)}
        confirmLoading={editLoading}
        okText="保存" cancelText="取消"
        destroyOnClose
      >
        <Form form={editForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序权重">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" style={{ width: '100%' }} tokenSeparators={[',']} placeholder="输入后 Enter 确认" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
