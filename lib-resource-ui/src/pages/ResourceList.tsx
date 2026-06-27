import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Table, Input, Tag, Space, message,
  Drawer, Collapse, Tooltip,
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

function ResourceDetail({ item, open, onClose }: {
  item: Resource | null; open: boolean; onClose: () => void
}) {
  if (!item) return null
  const thumb = item.thumbnail_path ?? item.file_path

  return (
    <Drawer
      title={<span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{item.name}</span>}
      open={open}
      onClose={onClose}
      width={460}
      destroyOnClose
      styles={{ body: { padding: '12px 20px 24px', overflowY: 'auto' } }}
    >
      {thumb && (
        <div style={{
          marginBottom: 16, borderRadius: 10, overflow: 'hidden',
          border: '1px solid #e2e8f0', background: '#f8fafc',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          maxHeight: 200,
        }}>
          <img
            src={`/static/${thumb}`}
            alt={item.name}
            style={{ maxWidth: '100%', maxHeight: 200, objectFit: 'contain', display: 'block' }}
          />
        </div>
      )}

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
      </div>
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
      render: (v: number) => <span style={{ color: '#94a3b8', fontSize: 12, fontFamily: 'ui-monospace,monospace' }}>{v}</span>,
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
            onClick: () => { setDetailItem(record); setDetailOpen(true) },
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
