import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Table, Input, Button, Tag, Space, message, Drawer, Tooltip, Collapse,
} from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api } from '../api'
import type { Resource } from '../types'

const PAGE_LIMIT = 20

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}

const dash = <span style={{ color: '#cbd5e1' }}>—</span>

function SectionHeader({ title }: { title: string }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 700, color: '#94a3b8',
      textTransform: 'uppercase' as const, letterSpacing: '0.08em',
      padding: '14px 0 6px', borderBottom: '1px solid #f1f5f9', marginBottom: 2,
    }}>
      {title}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', padding: '5px 0', gap: 12, alignItems: 'flex-start' }}>
      <div style={{ width: 76, flexShrink: 0, fontSize: 12, color: '#94a3b8', paddingTop: 2 }}>{label}</div>
      <div style={{ flex: 1, minWidth: 0, fontSize: 13, color: '#1e293b' }}>{children}</div>
    </div>
  )
}

function HashVal({ value }: { value: string | null | undefined }) {
  if (!value) return dash
  return (
    <Tooltip title={value} placement="topLeft">
      <code style={{
        fontFamily: 'ui-monospace,monospace', fontSize: 11,
        background: '#f1f5f9', padding: '2px 6px', borderRadius: 4,
        display: 'block', overflow: 'hidden', textOverflow: 'ellipsis',
        whiteSpace: 'nowrap', cursor: 'default', color: '#475569',
      }}>
        {value}
      </code>
    </Tooltip>
  )
}

// ── Detail Drawer ────────────────────────────────────────────────
function IconDetail({ item, open, onClose }: {
  item: Resource | null; open: boolean; onClose: () => void
}) {
  if (!item) return null

  return (
    <Drawer
      title={<span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{item.name}</span>}
      open={open}
      onClose={onClose}
      width={460}
      destroyOnClose
      styles={{ body: { padding: '12px 20px 24px', overflowY: 'auto' } }}
    >
      {/* ── 基础信息 ── */}
      <SectionHeader title="基础信息" />
      <Field label="ID"><span style={{ fontFamily: 'ui-monospace,monospace', fontSize: 12, color: '#94a3b8' }}>{item.id}</span></Field>
      <Field label="类型"><Tag style={{ margin: 0 }}>{item.resource_type_name}</Tag></Field>
      <Field label="名称">{item.name}</Field>
      <Field label="描述">{item.description ?? dash}</Field>
      <Field label="标签">
        {item.tags.length > 0
          ? <Space size={4} wrap>{item.tags.map(t => <Tag key={t} style={{ margin: 0 }}>{t}</Tag>)}</Space>
          : dash}
      </Field>
      <Field label="创建者">{item.created_by ?? dash}</Field>
      <Field label="排序">{item.sort_order}</Field>
      <Field label="创建时间">{item.created_at ? item.created_at.slice(0, 19).replace('T', ' ') : '—'}</Field>
      <Field label="更新时间">{item.updated_at ? item.updated_at.slice(0, 19).replace('T', ' ') : '—'}</Field>

      {/* ── 文件信息 ── */}
      <SectionHeader title="文件信息" />
      <Field label="文件名"><HashVal value={item.file_name} /></Field>
      <Field label="文件路径"><HashVal value={item.file_path} /></Field>
      <Field label="缩略图路径"><HashVal value={item.thumbnail_path} /></Field>
      <Field label="MIME">
        {item.mime_type
          ? <span style={{ fontFamily: 'ui-monospace,monospace', fontSize: 12 }}>{item.mime_type}</span>
          : dash}
      </Field>
      <Field label="大小">{item.file_size != null ? formatSize(item.file_size) : dash}</Field>
      <Field label="尺寸">
        {item.dimensions ? `${item.dimensions.width} × ${item.dimensions.height} px` : dash}
      </Field>

      {/* ── 图标信息 ── */}
      <SectionHeader title="图标信息" />
      <Field label="图标ID">
        {item.icon_id != null
          ? <span style={{ fontFamily: 'ui-monospace,monospace', fontSize: 12, color: '#64748b' }}>{item.icon_id}</span>
          : dash}
      </Field>
      <Field label="中文名">{item.icon_chinese_name ?? dash}</Field>
      <Field label="英文全称">{item.icon_name ?? dash}</Field>
      <Field label="英文名">{item.icon_english_name ?? dash}</Field>
      <Field label="分类">{item.icon_category ?? dash}</Field>

      {item.raw_data && (
        <Collapse
          ghost
          size="small"
          style={{ marginTop: 16 }}
          items={[{
            key: '1',
            label: <span style={{ fontSize: 12, color: '#94a3b8' }}>原始 JSON</span>,
            children: (
              <pre style={{
                background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6,
                padding: 10, fontSize: 11, overflow: 'auto', maxHeight: 240,
                fontFamily: 'ui-monospace,monospace', color: '#334155', margin: 0, lineHeight: 1.6,
              }}>
                {(() => { try { return JSON.stringify(JSON.parse(item.raw_data!), null, 2) } catch { return item.raw_data } })()}
              </pre>
            ),
          }]}
        />
      )}

      {/* ── 向量库映射 ── */}
      <div style={{
        marginTop: 20, padding: '14px 16px', borderRadius: 10,
        background: '#f8fafc', border: '1px solid #e2e8f0',
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          向量库映射
        </div>
        <Field label="向量文本">
          {item.vector_text
            ? <code style={{
                display: 'block', background: '#f1f5f9', border: '1px solid #e2e8f0',
                borderRadius: 5, padding: '5px 8px', fontSize: 12,
                fontFamily: 'ui-monospace,monospace', color: '#334155',
                wordBreak: 'break-all', lineHeight: 1.7,
              }}>{item.vector_text}</code>
            : dash}
        </Field>
        <div style={{ borderTop: '1px dashed #e2e8f0', margin: '10px 0 6px', opacity: 0.6 }} />
        <Field label="分类"><span style={{ color: '#334155' }}>{item.icon_category ?? dash}</span></Field>
        <Field label="中文名"><span style={{ fontWeight: 600, color: '#0f172a' }}>{item.icon_chinese_name ?? dash}</span></Field>
        <Field label="英文全称"><span style={{ color: '#334155' }}>{item.icon_name ?? dash}</span></Field>
        <Field label="英文名"><span style={{ color: '#334155' }}>{item.icon_english_name ?? dash}</span></Field>
        <Field label="描述"><span style={{ color: '#334155' }}>{item.description ?? '—'}</span></Field>
      </div>
    </Drawer>
  )
}

// ── IconList ─────────────────────────────────────────────────────
export interface IconListHandle { refresh: () => void }

interface Props {
  type: 'svg' | 'illustration'
  label: string
  extraActions?: React.ReactNode
  handleRef?: React.MutableRefObject<IconListHandle | null>
}

export default function IconList({ type, label, extraActions, handleRef }: Props) {
  const [items, setItems] = useState<Resource[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState(false)

  const [detailItem, setDetailItem] = useState<Resource | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const tableWrapRef = useRef<HTMLDivElement>(null)
  const [tableScrollY, setTableScrollY] = useState(400)

  useEffect(() => {
    const el = tableWrapRef.current
    if (!el) return
    const update = () => {
      const thead = el.querySelector<HTMLElement>('.ant-table-header')
      const pager = el.querySelector<HTMLElement>('.ant-table-pagination')
      setTableScrollY(Math.max(100, el.clientHeight - (thead?.offsetHeight ?? 48) - (pager?.offsetHeight ?? 56)))
    }
    update()
    const obs = new ResizeObserver(update)
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    if (searchMode) return
    let cancelled = false
    setLoading(true)
    api.listResources({ type, page, limit: PAGE_LIMIT })
      .then(data => {
        if (cancelled) return
        setItems(data.items)
        setTotal(data.total)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [type, page, searchMode, refreshKey])

  const handleSearch = useCallback(async (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) {
      setSearchMode(false)
      setPage(1)
      setRefreshKey(k => k + 1)
      return
    }
    setSearchMode(true)
    setLoading(true)
    try {
      const results = await api.vectorSearch({ query: trimmed, type, limit: 50 })
      setItems(results as Resource[])
      setTotal(results.length)
    } catch {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }, [type])

  const refresh = useCallback(() => {
    setSearchMode(false)
    setQuery('')
    setPage(1)
    setRefreshKey(k => k + 1)
  }, [])

  useEffect(() => {
    if (handleRef) handleRef.current = { refresh }
  })

  // ── 列定义 ───────────────────────────────────────────────────
  const baseColumns: ColumnsType<Resource> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 68,
      render: (v: number) => (
        <span style={{ color: '#94a3b8', fontSize: 12, fontFamily: 'ui-monospace,monospace' }}>{v}</span>
      ),
    },
    {
      title: '图标ID',
      width: 80,
      render: (_: unknown, r: Resource) => r.icon_id != null
        ? <span style={{ color: '#64748b', fontSize: 12, fontFamily: 'ui-monospace,monospace' }}>{r.icon_id}</span>
        : <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '中文名',
      dataIndex: 'name',
      width: 120,
      render: (v: string, r: Resource) => (
        <span style={{ fontWeight: 500, color: '#0f172a' }}>{r.icon_chinese_name ?? v}</span>
      ),
    },
    {
      title: '英文名',
      width: 140,
      render: (_: unknown, r: Resource) => r.icon_english_name
        ?? <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '分类',
      width: 110,
      render: (_: unknown, r: Resource) => r.icon_category
        ? <Tag style={{ margin: 0 }}>{r.icon_category}</Tag>
        : <span style={{ color: '#cbd5e1' }}>—</span>,
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
            {tags.map(t => <Tag key={t} style={{ margin: 0, borderRadius: 4, fontSize: 12 }}>{t}</Tag>)}
          </Space>
        ) : <span style={{ color: '#cbd5e1' }}>—</span>,
    },
  ]

  const scoreColumn: ColumnsType<Resource>[number] = {
    title: '相似度',
    dataIndex: 'score',
    width: 88,
    render: (v: number) => (
      <span style={{ fontWeight: 600, color: '#6366f1', fontFamily: 'ui-monospace,monospace' }}>
        {(v * 100).toFixed(1)}%
      </span>
    ),
  }

  const columns = searchMode ? [scoreColumn, ...baseColumns] : baseColumns

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ marginBottom: 20, flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>{label}</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
          {searchMode ? `搜索到 ${total} 条结果` : `共 ${total} 条数据`}
        </p>
      </div>

      <div
        style={{
          background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: '12px 16px', marginBottom: 14,
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', flexShrink: 0,
        }}
      >
        {extraActions && (
          <>
            {extraActions}
            <div style={{ width: 1, height: 20, background: '#e2e8f0' }} />
          </>
        )}

        <Input.Search
          placeholder={`向量搜索${label}`}
          allowClear
          value={query}
          onChange={e => setQuery(e.target.value)}
          onSearch={handleSearch}
          style={{ width: 280 }}
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          enterButton
        />

        {searchMode && (
          <Button
            onClick={() => { setQuery(''); handleSearch('') }}
            size="small"
            style={{ color: '#64748b' }}
          >
            返回全量
          </Button>
        )}
      </div>

      <div
        ref={tableWrapRef}
        style={{
          flex: 1, minHeight: 0,
          background: '#fff', borderRadius: 12,
          border: '1px solid #e2e8f0', overflow: 'hidden',
        }}
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={loading}
          size="middle"
          style={{ borderRadius: 0 }}
          scroll={{ y: tableScrollY }}
          onRow={record => ({ onClick: () => { setDetailItem(record); setDetailOpen(true) }, style: { cursor: 'pointer' } })}
          pagination={searchMode ? false : {
            current: page,
            pageSize: PAGE_LIMIT,
            total,
            onChange: setPage,
            showSizeChanger: false,
            showTotal: t => `共 ${t} 条`,
            style: { padding: '12px 20px' },
          }}
          locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无数据</div> }}
        />
      </div>

      <IconDetail
        item={detailItem}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </div>
  )
}
