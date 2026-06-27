import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Table, Input, Button, message, Drawer, Tooltip, Collapse,
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

// ── Drawer 内部小组件 ────────────────────────────────────────────
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

// ── Detail Drawer ────────────────────────────────────────────────
function ComponentDetail({ item, open, onClose }: {
  item: Resource | null; open: boolean; onClose: () => void
}) {
  if (!item) return null

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
      <Field label="领域">{item.cv_domain ?? dash}</Field>
      <Field label="组件类别">{item.cv_canvas_name ?? dash}</Field>
      <Field label="组件名">{item.cv_component_name ?? dash}</Field>
      <Field label="组件 GUID"><HashVal value={item.cv_component_guid} /></Field>
      <Field label="组件 Key"><HashVal value={item.cv_component_key} /></Field>
      <Field label="变体名">{item.cv_variant_name ?? dash}</Field>
      <Field label="变体 GUID"><HashVal value={item.cv_variant_guid} /></Field>
      <Field label="变体 Key"><HashVal value={item.cv_variant_key} /></Field>
      <Field label="变体属性">
        {item.cv_component_props?.length
          ? item.cv_component_props.map(p => `${p.name}: ${p.type}`).join('、')
          : dash}
      </Field>

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
        <Field label="组件名">
          <span style={{ fontWeight: 600, color: '#0f172a', fontSize: 13 }}>{item.cv_component_name ?? dash}</span>
        </Field>
        <Field label="组件类别">
          <span style={{ color: '#334155', fontSize: 13 }}>{item.cv_canvas_name ?? dash}</span>
        </Field>
        <Field label="变体名">
          <span style={{ color: '#334155', fontSize: 13 }}>{item.cv_variant_name ?? dash}</span>
        </Field>
      </div>

      {/* ── JSON 数据展开 ── */}
      {item.raw_data && (
        <Collapse
          ghost
          size="small"
          style={{ marginTop: 20 }}
          items={[{
            key: '1',
            label: <span style={{ fontSize: 12, color: '#94a3b8' }}>JSON 数据展开</span>,
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
    </Drawer>
  )
}

// ── ComponentList ────────────────────────────────────────────────
export interface ComponentListHandle { refresh: () => void }

interface Props {
  extraActions?: React.ReactNode
  handleRef?: React.MutableRefObject<ComponentListHandle | null>
}

export default function ComponentList({ handleRef }: Props) {
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
    api.listResources({ type: 'component_set', page, limit: PAGE_LIMIT })
      .then(data => { if (!cancelled) { setItems(data.items); setTotal(data.total) } })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [page, searchMode, refreshKey])

  const handleSearch = useCallback(async (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) {
      setSearchMode(false); setPage(1); setRefreshKey(k => k + 1)
      return
    }
    setSearchMode(true)
    setLoading(true)
    try {
      const results = await api.vectorSearch({ query: trimmed, type: 'component_set', limit: 50 })
      setItems(results as Resource[])
      setTotal(results.length)
    } catch { message.error('搜索失败') }
    finally { setLoading(false) }
  }, [])

  const refresh = useCallback(() => {
    setSearchMode(false); setQuery(''); setPage(1); setRefreshKey(k => k + 1)
  }, [])

  useEffect(() => { if (handleRef) handleRef.current = { refresh } })

  // ── 列定义 ───────────────────────────────────────────────────
  const baseColumns: ColumnsType<Resource> = [
    {
      title: 'ID', dataIndex: 'id', width: 68,
      render: (v: number) => v,
    },
    {
      title: '领域', width: 90,
      render: (_: unknown, r: Resource) => r.cv_domain ?? '—',
    },
    {
      title: '组件类别', width: 120,
      render: (_: unknown, r: Resource) => r.cv_canvas_name ?? '—',
    },
    {
      title: '组件名', width: 150,
      render: (_: unknown, r: Resource) => r.cv_component_name ?? '—',
    },
    {
      title: '变体名', ellipsis: true,
      render: (_: unknown, r: Resource) => r.cv_variant_name ?? '—',
    },
    {
      title: '标签', dataIndex: 'tags', width: 160,
      render: (tags: string[]) => tags.length ? tags.join('、') : '—',
    },
  ]

  const scoreColumn: ColumnsType<Resource>[number] = {
    title: '相似度', dataIndex: 'score', width: 88,
    render: (v: number) => `${(v * 100).toFixed(1)}%`,
  }

  const columns = searchMode ? [scoreColumn, ...baseColumns] : baseColumns

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ marginBottom: 20, flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>组件</h1>
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
          placeholder="向量搜索组件"
          allowClear
          value={query}
          onChange={e => setQuery(e.target.value)}
          onSearch={handleSearch}
          style={{ width: 280 }}
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          enterButton
        />
        {searchMode && (
          <Button onClick={() => { setQuery(''); handleSearch('') }} size="small" style={{ color: '#64748b' }}>
            返回全量
          </Button>
        )}
      </div>

      <div ref={tableWrapRef} style={{
        flex: 1, minHeight: 0, background: '#fff',
        borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden',
      }}>
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
            current: page, pageSize: PAGE_LIMIT, total, onChange: setPage,
            showSizeChanger: false, showTotal: t => `共 ${t} 条`,
            style: { padding: '12px 20px' },
          }}
          locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无数据</div> }}
        />
      </div>

      <ComponentDetail item={detailItem} open={detailOpen} onClose={() => setDetailOpen(false)} />
    </div>
  )
}
