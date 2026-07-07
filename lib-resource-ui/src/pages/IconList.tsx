import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Table, Input, Button, Select, message, Drawer, Tooltip, Image,
} from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api, staticUrl } from '../api'
import type { Resource } from '../types'

const DEFAULT_PAGE_SIZE = 20

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}

const dash = <span style={{ color: '#cbd5e1' }}>—</span>
const emptyCell = <span style={{ color: '#cbd5e1' }}>-</span>

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
function IconDetail({ item, open, onClose, onSaved }: {
  item: Resource | null; open: boolean; onClose: () => void; onSaved?: () => void
}) {
  const [name, setName] = useState(item?.name ?? '')
  const [description, setDescription] = useState(item?.description ?? '')
  const [tags, setTags] = useState<string[]>(item?.tags ?? [])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!item) return
    setName(item.name ?? '')
    setDescription(item.description ?? '')
    setTags(item.tags ?? [])
  }, [item])

  const handleSave = async () => {
    if (!item) return
    setSaving(true)
    try {
      await api.updateResource(item.id, { name, description, tags })
      message.success('保存成功')
      onSaved?.()
      onClose()
    } catch (e: unknown) {
      message.error('保存失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setSaving(false)
    }
  }

  if (!item) return null

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width="clamp(720px, 70%, 1100px)"
      destroyOnClose
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
        </div>
      }
      styles={{ body: { padding: '12px 20px 24px', overflowY: 'auto' } }}
    >
      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
      {/* ── 左侧预览图 ── */}
      <div style={{ width: 300, flexShrink: 0, position: 'sticky' as const, top: 0 }}>
        {item.thumbnail_path ? (
          <Image
            src={staticUrl(item.thumbnail_path)}
            width="100%"
            style={{ borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc' }}
          />
        ) : (
          <div style={{
            height: 260, borderRadius: 8, border: '1px dashed #e2e8f0',
            background: '#f8fafc', display: 'flex', alignItems: 'center',
            justifyContent: 'center', color: '#cbd5e1', fontSize: 13,
          }}>
            暂无预览图
          </div>
        )}
      </div>

      {/* ── 右侧字段列表 ── */}
      <div style={{ flex: 1, minWidth: 0 }}>
      {/* ── 基础信息 ── */}
      <SectionHeader title="基础信息" />
      <Field label="ID">{item.id}</Field>
      <Field label="名称">
        <Input value={name} onChange={e => setName(e.target.value)} size="small" />
      </Field>
      <Field label="描述">
        <Input.TextArea
          value={description}
          onChange={e => setDescription(e.target.value)}
          autoSize={{ minRows: 2, maxRows: 5 }}
          size="small"
        />
      </Field>
      <Field label="标签">
        <Select
          mode="tags"
          value={tags}
          onChange={setTags}
          style={{ width: '100%' }}
          size="small"
          placeholder="输入后回车添加"
          tokenSeparators={[',']}
        />
      </Field>
      <Field label="创建时间">{item.created_at ? item.created_at.slice(0, 19).replace('T', ' ') : '—'}</Field>
      <Field label="更新时间">{item.updated_at ? item.updated_at.slice(0, 19).replace('T', ' ') : '—'}</Field>
      <Field label="文件名"><HashVal value={item.file_name} /></Field>
      <Field label="文件路径"><HashVal value={item.file_path} /></Field>
      <Field label="缩略图路径"><HashVal value={item.thumbnail_path} /></Field>
      <Field label="文件类型">{item.mime_type ?? dash}</Field>
      <Field label="文件大小">{item.file_size != null ? formatSize(item.file_size) : dash}</Field>
      <Field label="资源宽度">{item.width != null ? `${item.width} px` : dash}</Field>
      <Field label="资源高度">{item.height != null ? `${item.height} px` : dash}</Field>
      <Field label="图标ID">{item.icon_id != null ? item.icon_id : dash}</Field>
      <Field label="中文名">{item.icon_chinese_name ?? dash}</Field>
      <Field label="英文全称">{item.icon_name ?? dash}</Field>
      <Field label="英文名">{item.icon_english_name ?? dash}</Field>
      <Field label="分类">{item.icon_category ?? dash}</Field>
      <Field label="领域">{item.icon_group ?? dash}</Field>

      {/* ── 向量库映射 ── */}
      <SectionHeader title="向量库映射" />
      <Field label="向量文本">{item.vector_text || dash}</Field>
      <Field label="分类">{item.icon_category ?? dash}</Field>
      <Field label="中文名">{item.icon_chinese_name ?? dash}</Field>
      <Field label="英文全称">{item.icon_name ?? dash}</Field>
      <Field label="英文名">{item.icon_english_name ?? dash}</Field>
      <Field label="描述">{item.description ?? dash}</Field>
      <Field label="标签">{item.tags.length > 0 ? item.tags.join('、') : dash}</Field>

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
      </div>
      </div>
    </Drawer>
  )
}

// ── IconList ─────────────────────────────────────────────────────
export interface IconListHandle { refresh: () => void }

interface Props {
  type: 'icon' | 'illus'
  label: string
  extraActions?: React.ReactNode
  handleRef?: React.MutableRefObject<IconListHandle | null>
}

export default function IconList({ type, label, handleRef }: Props) {
  const [items, setItems] = useState<Resource[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [loading, setLoading] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState(false)

  const [filters, setFilters] = useState<Record<string, string[] | null>>({})
  const [filterOptions, setFilterOptions] = useState<Record<string, string[]>>({})

  const [detailItem, setDetailItem] = useState<Resource | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)

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
    api.getFilterOptions(type)
      .then(data => setFilterOptions(data.options))
      .catch(() => {})
  }, [type, refreshKey])

  useEffect(() => {
    if (searchMode) return
    let cancelled = false
    setLoading(true)
    api.listResources({ type, page, limit: pageSize, filters })
      .then(data => {
        if (cancelled) return
        setItems(data.items)
        setTotal(data.total)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [type, page, pageSize, searchMode, refreshKey, filters])

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
  const filterProps = (field: string) => searchMode ? {} : {
    key: field,
    filters: (filterOptions[field] ?? []).map(v => ({ text: v, value: v })),
    filteredValue: filters[field] ?? null,
    filterSearch: true,
  }

  const baseColumns: ColumnsType<Resource> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 68,
      render: (v: number) => v,
    },
    {
      title: '缩略图',
      width: 80,
      render: (_: unknown, r: Resource) => {
        if (!r.thumbnail_path) return emptyCell
        return (
          <Image
            src={staticUrl(r.thumbnail_path)}
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
      title: '图标ID',
      width: 80,
      ellipsis: { showTitle: false },
      render: (_: unknown, r: Resource) => {
        if (r.icon_id == null) return emptyCell
        const text = String(r.icon_id)
        return <Tooltip title={text} placement="topLeft">{text}</Tooltip>
      },
    },
    {
      title: '中文名',
      dataIndex: 'name',
      width: 160,
      ellipsis: { showTitle: false },
      render: (v: string, r: Resource) => {
        const text = r.icon_chinese_name ?? v
        if (!text) return emptyCell
        return <Tooltip title={text} placement="topLeft">{text}</Tooltip>
      },
    },
    {
      title: '英文名',
      width: 180,
      ellipsis: { showTitle: false },
      render: (_: unknown, r: Resource) => {
        if (!r.icon_english_name) return emptyCell
        return <Tooltip title={r.icon_english_name} placement="topLeft">{r.icon_english_name}</Tooltip>
      },
    },
    {
      title: '分类',
      width: 110,
      ellipsis: { showTitle: false },
      ...filterProps('icon_category'),
      render: (_: unknown, r: Resource) => {
        if (!r.icon_category) return emptyCell
        return <Tooltip title={r.icon_category} placement="topLeft">{r.icon_category}</Tooltip>
      },
    },
    {
      title: '领域',
      width: 110,
      ellipsis: { showTitle: false },
      ...filterProps('icon_group'),
      render: (_: unknown, r: Resource) => {
        if (!r.icon_group) return emptyCell
        return <Tooltip title={r.icon_group} placement="topLeft">{r.icon_group}</Tooltip>
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: { showTitle: false },
      render: (v: string | null) => {
        if (!v) return emptyCell
        return <Tooltip title={v} placement="topLeft">{v}</Tooltip>
      },
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 160,
      ellipsis: { showTitle: false },
      render: (tags: string[]) => {
        if (!tags.length) return emptyCell
        const text = tags.join('、')
        return <Tooltip title={text} placement="topLeft">{text}</Tooltip>
      },
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
          onRow={record => ({ onClick: () => { if (!isPreviewing) { setDetailItem(record); setDetailOpen(true) } }, style: { cursor: 'pointer' } })}
          onChange={(_, tableFilters, __, extra) => {
            if (extra.action === 'filter') {
              setPage(1)
              setFilters(tableFilters as Record<string, string[] | null>)
            }
          }}
          pagination={searchMode ? false : {
            current: page,
            pageSize,
            total,
            onChange: setPage,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
            onShowSizeChange: (_: number, size: number) => { setPage(1); setPageSize(size) },
            showQuickJumper: true,
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
        onSaved={refresh}
      />
    </div>
  )
}
