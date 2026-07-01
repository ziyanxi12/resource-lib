import { useState, useEffect, useCallback, useRef } from 'react'
import { Table, Input, Button, message, Drawer, Tooltip } from 'antd'
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
      <span style={{
        display: 'block', overflow: 'hidden', textOverflow: 'ellipsis',
        whiteSpace: 'nowrap', cursor: 'default',
      }}>
        {value}
      </span>
    </Tooltip>
  )
}

function IllusDetail({ item, open, onClose }: {
  item: Resource | null; open: boolean; onClose: () => void
}) {
  if (!item) return null
  const tags = item.illus_tags?.length ? item.illus_tags.join('、') : '—'

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width={640}
      destroyOnClose
      styles={{ body: { padding: '12px 20px 24px', overflowY: 'auto' } }}
    >
      {/* ── 基础信息 ── */}
      <SectionHeader title="基础信息" />
      <Field label="ID">{item.id}</Field>
      <Field label="名称">{item.name}</Field>
      <Field label="描述">{item.description ?? dash}</Field>
      <Field label="标签">{item.tags.length > 0 ? item.tags.join('、') : dash}</Field>
      <Field label="创建时间">{item.created_at ? item.created_at.slice(0, 19).replace('T', ' ') : '—'}</Field>
      <Field label="更新时间">{item.updated_at ? item.updated_at.slice(0, 19).replace('T', ' ') : '—'}</Field>
      <Field label="文件名"><HashVal value={item.file_name} /></Field>
      <Field label="文件路径"><HashVal value={item.file_path} /></Field>
      <Field label="缩略图路径"><HashVal value={item.thumbnail_path} /></Field>
      <Field label="文件类型">{item.mime_type ?? dash}</Field>
      <Field label="文件大小">{item.file_size != null ? formatSize(item.file_size) : dash}</Field>
      <Field label="资源尺寸">
        {item.dimensions ? `${item.dimensions.width} × ${item.dimensions.height} px` : dash}
      </Field>
      <Field label="插画ID"><HashVal value={item.illus_id} /></Field>
      <Field label="分类">{item.illus_category ?? dash}</Field>
      <Field label="插画标签">{tags !== '—' ? tags : dash}</Field>
      <Field label="版本">{item.illus_version ?? dash}</Field>

      {/* ── 向量库映射 ── */}
      <SectionHeader title="向量库映射" />
      <Field label="向量文本">{item.vector_text || dash}</Field>
      <Field label="插画ID">{item.illus_id ?? dash}</Field>
      <Field label="名称">{item.name ?? dash}</Field>
      <Field label="描述">{item.description ?? dash}</Field>
      <Field label="分类">{item.illus_category ?? dash}</Field>
      <Field label="标签">{item.illus_tags?.join?.(', ') ?? item.illus_tags ?? dash}</Field>
      <Field label="版本">{item.illus_version ?? dash}</Field>

      {/* ── JSON 数据 ── */}
      {item.raw_data && (
        <>
          <SectionHeader title="原始JSON" />
          <pre style={{
            fontSize: 11,
            fontFamily: 'ui-monospace,monospace', color: '#334155', margin: 0, lineHeight: 1.6,
          }}>
            {(() => { try { return JSON.stringify(JSON.parse(item.raw_data!), null, 2) } catch { return item.raw_data } })()}
          </pre>
        </>
      )}
    </Drawer>
  )
}

// ── IllusList ────────────────────────────────────────────────────
export interface IllusListHandle { refresh: () => void }

interface Props {
  handleRef?: React.MutableRefObject<IllusListHandle | null>
  extraActions?: React.ReactNode
}

export default function IllusList({ handleRef, extraActions }: Props) {
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
    api.listResources({ type: 'illus', page, limit: PAGE_LIMIT })
      .then(data => {
        if (cancelled) return
        setItems(data.items)
        setTotal(data.total)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [page, searchMode, refreshKey])

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
      const results = await api.vectorSearch({ query: trimmed, type: 'illus', limit: 50 })
      setItems(results as Resource[])
      setTotal(results.length)
    } catch {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const refresh = useCallback(() => {
    setSearchMode(false)
    setQuery('')
    setPage(1)
    setRefreshKey(k => k + 1)
  }, [])

  useEffect(() => {
    if (handleRef) handleRef.current = { refresh }
  })

  const baseColumns: ColumnsType<Resource> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 68,
    },
    {
      title: '插画ID',
      width: 110,
      render: (_: unknown, r: Resource) => r.illus_id ?? '—',
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 130,
    },
    {
      title: '分类',
      width: 110,
      render: (_: unknown, r: Resource) => r.illus_category ?? '—',
    },
    {
      title: '标签',
      width: 160,
      render: (_: unknown, r: Resource) =>
        r.illus_tags?.length ? r.illus_tags.join('、') : '—',
    },
    {
      title: '版本',
      width: 80,
      render: (_: unknown, r: Resource) => r.illus_version ?? '—',
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string | null) => v ?? '—',
    },
  ]

  const scoreColumn: ColumnsType<Resource>[number] = {
    title: '相似度',
    dataIndex: 'score',
    width: 88,
    render: (v: number) => `${(v * 100).toFixed(1)}%`,
  }

  const columns = searchMode ? [scoreColumn, ...baseColumns] : baseColumns

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ marginBottom: 20, flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>插画</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
          {searchMode ? `搜索到 ${total} 条结果` : `共 ${total} 条数据`}
        </p>
      </div>

      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
        padding: '12px 16px', marginBottom: 14,
        display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', flexShrink: 0,
      }}>
        <Input.Search
          placeholder="向量搜索插画"
          allowClear
          value={query}
          onChange={e => setQuery(e.target.value)}
          onSearch={handleSearch}
          style={{ width: 280 }}
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          enterButton
        />
        {extraActions}
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

      <IllusDetail
        item={detailItem}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </div>
  )
}
