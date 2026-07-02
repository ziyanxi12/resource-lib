import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Table, Input, message,
  Drawer, Tooltip, Image,
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
      <span style={{
        display: 'block', overflow: 'hidden', textOverflow: 'ellipsis',
        whiteSpace: 'nowrap', cursor: 'default',
      }}>
        {value}
      </span>
    </Tooltip>
  )
}

function ResourceDetail({ item, open, onClose }: {
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

      {/* ── 向量库映射 ── */}
      <SectionHeader title="向量库映射" />
      <Field label="向量文本">{item.vector_text || dash}</Field>
      <Field label="名称">{item.name ?? dash}</Field>
      <Field label="描述">{item.description ?? dash}</Field>

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

// ── ResourceList ─────────────────────────────────────────────────
export interface ResourceListHandle { refresh: () => void }

interface Props {
  type: string
  label: string
  extraActions?: React.ReactNode
  handleRef?: React.MutableRefObject<ResourceListHandle | null>
}

export default function ResourceList({ type, label, handleRef }: Props) {
  const [search, setSearch] = useState('')

  const [detailItem, setDetailItem] = useState<Resource | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)

  const [tPage, setTPage] = useState(1)
  const [tTotal, setTTotal] = useState(0)
  const [tItems, setTItems] = useState<Resource[]>([])
  const [tLoading, setTLoading] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

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
    let cancelled = false
    setTLoading(true)
    api.listResources({ type, page: tPage, limit: PAGE_LIMIT, search: search || undefined })
      .then(data => {
        if (cancelled) return
        setTItems(data.items)
        setTTotal(data.total)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setTLoading(false) })
    return () => { cancelled = true }
  }, [type, tPage, search, refreshKey])

  const refresh = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  useEffect(() => {
    if (handleRef) handleRef.current = { refresh }
  })

  const columns: ColumnsType<Resource> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 72,
      render: (v: number) => v,
    },
    {
      title: '缩略图',
      width: 80,
      render: (_: unknown, r: Resource) => {
        if (!r.thumbnail_path) return '—'
        return (
          <Image
            src={`/static/${r.thumbnail_path}`}
            width={48}
            height={48}
            style={{ borderRadius: 6, objectFit: 'cover' }}
            onClick={(e) => e.stopPropagation()}
            preview={{
              onVisibleChange: (visible: boolean) => setIsPreviewing(visible)
            }}
          />
        )
      }
    },
    {
      title: '名称',
      dataIndex: 'name',
      render: (name: string) => name,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string | null) => v ?? '—',
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 200,
      render: (tags: string[]) => tags.length ? tags.join('、') : '—',
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ marginBottom: 20, flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>{label}</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>共 {tTotal} 条数据</p>
      </div>

      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
        padding: '12px 16px', marginBottom: 14,
        display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0,
      }}>
        <Input.Search
          placeholder="搜索名称 / 描述"
          allowClear
          style={{ width: 280 }}
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          enterButton
          onSearch={v => { setSearch(v); setTPage(1) }}
        />
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
          dataSource={tItems}
          loading={tLoading}
          size="middle"
          style={{ borderRadius: 0 }}
          scroll={{ y: tableScrollY }}
          onRow={record => ({
            onClick: () => { if (!isPreviewing) { setDetailItem(record); setDetailOpen(true) } },
            style: { cursor: 'pointer' },
          })}
          pagination={{
            current: tPage,
            pageSize: PAGE_LIMIT,
            total: tTotal,
            onChange: setTPage,
            showSizeChanger: false,
            showTotal: t => `共 ${t} 条`,
            style: { padding: '12px 20px' },
          }}
          locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无数据</div> }}
        />
      </div>

      <ResourceDetail
        item={detailItem}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </div>
  )
}
