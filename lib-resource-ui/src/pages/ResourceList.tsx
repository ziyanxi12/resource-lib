import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Table, Input, Select, Button, Tooltip, Tag, Space, message, Spin,
  Drawer, Descriptions,
} from 'antd'
import { TableOutlined, AppstoreOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api } from '../api'
import type { Resource } from '../types'

const TABLE_LIMIT = 20
const CARD_LIMIT = 24

// ── Detail Drawer ────────────────────────────────────────────────
function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}

function ResourceDetail({ item, open, onClose }: {
  item: Resource | null; open: boolean; onClose: () => void
}) {
  if (!item) return null
  const thumb = item.thumbnail_path ?? item.file_path

  return (
    <Drawer
      title={
        <div style={{ fontWeight: 700, fontSize: 16, color: '#0f172a' }}>{item.name}</div>
      }
      open={open}
      onClose={onClose}
      width={560}
      destroyOnClose
      styles={{ body: { padding: '20px 24px' } }}
    >
      {/* Preview image */}
      {thumb && (
        <div
          style={{
            marginBottom: 20, borderRadius: 10, overflow: 'hidden',
            border: '1px solid #e2e8f0', background: '#f8fafc',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            maxHeight: 220,
          }}
        >
          <img
            src={`/static/${thumb}`}
            alt={item.name}
            style={{ maxWidth: '100%', maxHeight: 220, objectFit: 'contain', display: 'block' }}
          />
        </div>
      )}

      {/* Core fields */}
      <Descriptions bordered column={2} size="small" labelStyle={{ color: '#64748b', whiteSpace: 'nowrap' }}>
        <Descriptions.Item label="ID">
          <span style={{ color: '#94a3b8', fontFamily: 'ui-monospace,monospace' }}>#{item.id}</span>
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          <Tag style={{ margin: 0 }}>{item.resource_type_name}</Tag>
        </Descriptions.Item>

        <Descriptions.Item label="名称" span={2}>{item.name}</Descriptions.Item>

        {item.description && (
          <Descriptions.Item label="描述" span={2}>{item.description}</Descriptions.Item>
        )}

        {item.tags.length > 0 && (
          <Descriptions.Item label="标签" span={2}>
            <Space size={4} wrap>
              {item.tags.map(t => <Tag key={t} style={{ margin: 0 }}>{t}</Tag>)}
            </Space>
          </Descriptions.Item>
        )}

        {item.file_name && (
          <Descriptions.Item label="文件名" span={2}>
            <code style={{ fontSize: 12, background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>
              {item.file_name}
            </code>
          </Descriptions.Item>
        )}

        {item.file_path && (
          <Descriptions.Item label="文件路径" span={2}>
            <code style={{ fontSize: 12, background: '#f1f5f9', padding: '1px 6px', borderRadius: 4, wordBreak: 'break-all' }}>
              {item.file_path}
            </code>
          </Descriptions.Item>
        )}

        {item.thumbnail_path && (
          <Descriptions.Item label="缩略图路径" span={2}>
            <code style={{ fontSize: 12, background: '#f1f5f9', padding: '1px 6px', borderRadius: 4, wordBreak: 'break-all' }}>
              {item.thumbnail_path}
            </code>
          </Descriptions.Item>
        )}

        {item.mime_type && (
          <Descriptions.Item label="MIME 类型" span={item.file_size ? 1 : 2}>
            <span style={{ fontFamily: 'ui-monospace,monospace', fontSize: 12 }}>{item.mime_type}</span>
          </Descriptions.Item>
        )}

        {item.file_size != null && (
          <Descriptions.Item label="文件大小" span={item.mime_type ? 1 : 2}>
            {formatSize(item.file_size)}
          </Descriptions.Item>
        )}

        {item.dimensions && (
          <Descriptions.Item label="尺寸" span={2}>
            {item.dimensions.width} × {item.dimensions.height} px
          </Descriptions.Item>
        )}

        {item.created_by && (
          <Descriptions.Item label="创建者">{item.created_by}</Descriptions.Item>
        )}

        <Descriptions.Item label="排序权重">{item.sort_order}</Descriptions.Item>

        <Descriptions.Item label="创建时间">
          {item.created_at ? item.created_at.slice(0, 19).replace('T', ' ') : '—'}
        </Descriptions.Item>
        <Descriptions.Item label="更新时间">
          {item.updated_at ? item.updated_at.slice(0, 19).replace('T', ' ') : '—'}
        </Descriptions.Item>
      </Descriptions>

      {/* raw_data */}
      {item.raw_data && (() => {
        let parsed: unknown = null
        try { parsed = JSON.parse(item.raw_data) } catch { /* not valid JSON */ }
        return (
          <div style={{ marginTop: 20 }}>
            <div style={{ marginBottom: 8, fontWeight: 600, fontSize: 13, color: '#475569' }}>原始数据</div>
            <pre
              style={{
                background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                padding: 14, fontSize: 12, overflow: 'auto', maxHeight: 320,
                fontFamily: 'ui-monospace,monospace', color: '#334155', margin: 0, lineHeight: 1.6,
              }}
            >
              {parsed ? JSON.stringify(parsed, null, 2) : item.raw_data}
            </pre>
          </div>
        )
      })()}
    </Drawer>
  )
}

// ── Card for grid view ───────────────────────────────────────────
function ResourceCard({ item, onClick }: { item: Resource; onClick: () => void }) {
  const [hov, setHov] = useState(false)
  const thumb = item.thumbnail_path ?? item.file_path

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: '#fff',
        borderRadius: 12,
        overflow: 'hidden',
        border: `1.5px solid ${hov ? '#c7d2fe' : '#e2e8f0'}`,
        transition: 'all 0.18s',
        transform: hov ? 'translateY(-2px)' : 'none',
        boxShadow: hov ? '0 8px 24px rgba(99,102,241,0.12)' : '0 1px 3px rgba(0,0,0,0.04)',
        cursor: 'pointer',
      }}
    >
      {/* Preview */}
      <div style={{ height: 130, background: '#f8fafc', overflow: 'hidden' }}>
        {thumb ? (
          <img
            src={`/static/${thumb}`}
            alt={item.name}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <div
            style={{
              width: '100%', height: '100%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'linear-gradient(135deg,#eef2ff,#f5f3ff)',
              color: '#6366f1', fontSize: 32, fontWeight: 800,
            }}
          >
            {item.name.slice(0, 2).toUpperCase()}
          </div>
        )}
      </div>

      {/* Info */}
      <div style={{ padding: '10px 12px 12px' }}>
        <div style={{ fontWeight: 600, fontSize: 13, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {item.name}
        </div>
        {item.description && (
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.description}
          </div>
        )}
        {item.tags.length > 0 && (
          <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {item.tags.slice(0, 3).map(t => (
              <Tag key={t} style={{ margin: 0, fontSize: 11, borderRadius: 4, padding: '0 5px', lineHeight: '18px' }}>{t}</Tag>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── ResourceList ─────────────────────────────────────────────────
export interface ResourceListHandle { refresh: () => void }

interface Props {
  type: string
  label: string
  extraActions?: React.ReactNode
  handleRef?: React.MutableRefObject<ResourceListHandle | null>
}

export default function ResourceList({ type, label, extraActions, handleRef }: Props) {
  const [view, setView] = useState<'table' | 'card'>('table')
  const [search, setSearch] = useState('')
  const [tagFilter, setTagFilter] = useState<string | undefined>()
  const [allTags, setAllTags] = useState<string[]>([])

  // Detail drawer
  const [detailItem, setDetailItem] = useState<Resource | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  // Table state
  const [tPage, setTPage] = useState(1)
  const [tTotal, setTTotal] = useState(0)
  const [tItems, setTItems] = useState<Resource[]>([])
  const [tLoading, setTLoading] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  // Table height — measured by ResizeObserver so pagination stays in view
  const tableWrapRef = useRef<HTMLDivElement>(null)
  const [tableScrollY, setTableScrollY] = useState(400)

  // Card state
  const [cItems, setCItems] = useState<Resource[]>([])
  const [cHasMore, setCHasMore] = useState(true)
  const [cLoading, setCLoading] = useState(false)
  const cLoadingRef = useRef(false)
  const cHasMoreRef = useRef(true)
  const cPageRef = useRef(0)
  const cGenRef = useRef(0)
  const sentinelRef = useRef<HTMLDivElement>(null)

  // Collect tags for filter dropdown
  const addTags = useCallback((items: Resource[]) => {
    const tags: string[] = []
    items.forEach(r => r.tags.forEach(t => { if (!tags.includes(t)) tags.push(t) }))
    if (tags.length > 0) setAllTags(prev => [...new Set([...prev, ...tags])])
  }, [])

  // ── Measure table wrapper ────────────────────────────────────
  useEffect(() => {
    if (view !== 'table') return
    const el = tableWrapRef.current
    if (!el) return
    const update = () => {
      const thead = el.querySelector<HTMLElement>('.ant-table-header')
      const pager = el.querySelector<HTMLElement>('.ant-table-pagination')
      const theadH = thead?.offsetHeight ?? 48
      const pagerH = pager?.offsetHeight ?? 56
      setTableScrollY(Math.max(100, el.clientHeight - theadH - pagerH))
    }
    update()
    const obs = new ResizeObserver(update)
    obs.observe(el)
    return () => obs.disconnect()
  }, [view])

  // ── Table fetch ──────────────────────────────────────────────
  useEffect(() => {
    if (view !== 'table') return
    let cancelled = false
    setTLoading(true)
    api.listResources({ type, page: tPage, limit: TABLE_LIMIT, search: search || undefined })
      .then(data => {
        if (cancelled) return
        setTItems(data.items)
        setTTotal(data.total)
        addTags(data.items)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setTLoading(false) })
    return () => { cancelled = true }
  }, [view, type, tPage, search, refreshKey, addTags])

  // ── Card load ────────────────────────────────────────────────
  const loadCards = useCallback((q: string, gen: number) => {
    if (cLoadingRef.current || !cHasMoreRef.current) return
    cLoadingRef.current = true
    setCLoading(true)
    const nextPage = cPageRef.current + 1
    api.listResources({ type, page: nextPage, limit: CARD_LIMIT, search: q || undefined })
      .then(data => {
        if (gen !== cGenRef.current) return
        cPageRef.current = nextPage
        const hasMore = data.items.length === CARD_LIMIT
        cHasMoreRef.current = hasMore
        setCHasMore(hasMore)
        setCItems(prev => nextPage === 1 ? data.items : [...prev, ...data.items])
        addTags(data.items)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => {
        if (gen === cGenRef.current) { cLoadingRef.current = false; setCLoading(false) }
      })
  }, [type, addTags])

  const resetCards = useCallback((q: string) => {
    cGenRef.current++
    cPageRef.current = 0
    cLoadingRef.current = false
    cHasMoreRef.current = true
    setCItems([])
    setCHasMore(true)
    setCLoading(false)
    loadCards(q, cGenRef.current)
  }, [loadCards])

  useEffect(() => {
    if (view === 'card') resetCards(search)
  }, [view, search, resetCards])

  // ── IntersectionObserver ─────────────────────────────────────
  useEffect(() => {
    if (view !== 'card') return
    const sentinel = sentinelRef.current
    if (!sentinel) return
    const q = search
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) loadCards(q, cGenRef.current) },
      { rootMargin: '150px' }
    )
    obs.observe(sentinel)
    return () => obs.disconnect()
  }, [view, search, loadCards])

  // ── Expose refresh ───────────────────────────────────────────
  const refresh = useCallback(() => {
    if (view === 'table') setRefreshKey(k => k + 1)
    else resetCards(search)
  }, [view, resetCards, search])

  useEffect(() => {
    if (handleRef) handleRef.current = { refresh }
  })

  const openDetail = (item: Resource) => {
    setDetailItem(item)
    setDetailOpen(true)
  }

  const switchView = (v: 'table' | 'card') => {
    setView(v)
    setTPage(1)
    setTagFilter(undefined)
  }

  // ── Columns (id / name / description / tags) ─────────────────
  const columns: ColumnsType<Resource> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 72,
      render: (v: number) => <span style={{ color: '#94a3b8', fontSize: 12, fontFamily: 'ui-monospace,monospace' }}>#{v}</span>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      render: (name: string) => (
        <div style={{ fontWeight: 500, color: '#0f172a' }}>{name}</div>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string | null) => v ?? <span style={{ color: '#e2e8f0' }}>—</span>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 200,
      render: (tags: string[]) =>
        tags.length ? (
          <Space size={4} wrap>
            {tags.map(t => <Tag key={t} style={{ margin: 0, borderRadius: 4, fontSize: 12 }}>{t}</Tag>)}
          </Space>
        ) : <span style={{ color: '#e2e8f0' }}>—</span>,
    },
  ]

  // Client-side tag filter
  const filteredTable = tagFilter ? tItems.filter(i => i.tags.includes(tagFilter)) : tItems
  const filteredCards = tagFilter ? cItems.filter(i => i.tags.includes(tagFilter)) : cItems

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* Header */}
      <div style={{ marginBottom: 20, flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>{label}</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>共 {tTotal} 条数据</p>
      </div>

      {/* Toolbar */}
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          padding: '12px 16px',
          marginBottom: 14,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          flexWrap: 'wrap',
          flexShrink: 0,
        }}
      >
        {extraActions && (
          <>
            {extraActions}
            <div style={{ width: 1, height: 20, background: '#e2e8f0' }} />
          </>
        )}

        <Select
          allowClear
          placeholder="按标签筛选"
          style={{ width: 160 }}
          value={tagFilter}
          onChange={setTagFilter}
          options={allTags.map(t => ({ label: t, value: t }))}
        />

        <Input.Search
          placeholder="搜索名称 / 描述"
          allowClear
          style={{ width: 240 }}
          onSearch={v => { setSearch(v); setTPage(1) }}
        />

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
          <Tooltip title="表格视图">
            <Button
              type={view === 'table' ? 'primary' : 'text'}
              icon={<TableOutlined />}
              onClick={() => switchView('table')}
              style={{ borderRadius: 0, border: 'none' }}
            />
          </Tooltip>
          <Tooltip title="卡片视图">
            <Button
              type={view === 'card' ? 'primary' : 'text'}
              icon={<AppstoreOutlined />}
              onClick={() => switchView('card')}
              style={{ borderRadius: 0, border: 'none', borderLeft: '1px solid #e2e8f0' }}
            />
          </Tooltip>
        </div>
      </div>

      {/* ── Table view ── */}
      {view === 'table' && (
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
            dataSource={filteredTable}
            loading={tLoading}
            size="middle"
            style={{ borderRadius: 0 }}
            scroll={{ y: tableScrollY }}
            onRow={record => ({
              onClick: () => openDetail(record),
              style: { cursor: 'pointer' },
            })}
            pagination={{
              current: tPage,
              pageSize: TABLE_LIMIT,
              total: tTotal,
              onChange: setTPage,
              showSizeChanger: false,
              showTotal: t => `共 ${t} 条`,
              style: { padding: '12px 20px' },
            }}
            locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无数据</div> }}
          />
        </div>
      )}

      {/* ── Card view ── */}
      {view === 'card' && (
        <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          {filteredCards.length === 0 && !cLoading && (
            <div style={{ textAlign: 'center', padding: '80px 0', color: '#94a3b8', fontSize: 14 }}>
              暂无数据
            </div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
            {filteredCards.map(item => (
              <ResourceCard key={item.id} item={item} onClick={() => openDetail(item)} />
            ))}
          </div>

          <div
            ref={sentinelRef}
            style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 8 }}
          >
            {cLoading && <Spin />}
            {!cHasMore && cItems.length > 0 && (
              <span style={{ color: '#cbd5e1', fontSize: 13 }}>已加载全部 {cItems.length} 条</span>
            )}
          </div>
        </div>
      )}

      {/* ── Detail Drawer ── */}
      <ResourceDetail
        item={detailItem}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </div>
  )
}
