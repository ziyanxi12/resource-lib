import { useState, useEffect, useCallback, useRef } from 'react'
import { Table, Input, Button, Drawer, Tooltip, Image, message, Select, TreeSelect, Modal, Upload } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { TreeSelectProps } from 'antd'
import { api, staticUrl } from '../api'
import type { Resource } from '../types'
import type { GroupNode } from '../api'
import SemanticUnderstand from './SemanticUnderstand'

const DEFAULT_PAGE_SIZE = 20

const emptyCell = <span style={{ color: '#cbd5e1' }}>-</span>

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}

function formatDateTime(dt: string | null | undefined): string {
  if (!dt) return '-'
  return dt.slice(0, 19).replace('T', ' ')
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 700, color: '#94a3b8',
      textTransform: 'uppercase' as const, letterSpacing: '0.08em',
      padding: '14px 0 6px', borderBottom: '1px solid #f1f5f9', marginBottom: 8, marginTop: 16,
    }}>
      {title}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', padding: '5px 0', gap: 12, alignItems: 'flex-start' }}>
      <div style={{ width: 80, flexShrink: 0, fontSize: 12, color: '#94a3b8', paddingTop: 2 }}>{label}</div>
      <div style={{ flex: 1, minWidth: 0, fontSize: 13, color: '#1e293b' }}>{children}</div>
    </div>
  )
}

function DetailDrawer({ item, open, onClose, onSaved, type }: {
  item: Resource | null
  open: boolean
  onClose: () => void
  onSaved?: () => void
  type: string
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [searchText, setSearchText] = useState('')
  const [fileName, setFileName] = useState('')
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  
  const [prompt, setPrompt] = useState('')
  const [semanticText, setSemanticText] = useState('')
  
  const [newThumbnail, setNewThumbnail] = useState<File | null>(null)
  const [newFile, setNewFile] = useState<File | null>(null)
  
  const [groupTreeData, setGroupTreeData] = useState<TreeSelectProps['treeData']>([])
  const thumbnailInputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!item) return
    setName(item.name ?? '')
    setDescription(item.description ?? '')
    setTags(item.tags ?? [])
    setSearchText(item.search_text ?? '')
    setFileName(item.file_name ?? '')
    setSelectedGroupId(item.group_id)
    setSemanticText('')
    setPrompt('')
    setNewThumbnail(null)
    setNewFile(null)
  }, [item])

  useEffect(() => {
    if (!open || !item) return
    api.getGroups(type, item.source_id, false).then(data => {
      const convertToTreeData = (nodes: GroupNode[]): TreeSelectProps['treeData'] => 
        nodes.map(node => ({
          value: node.id,
          title: node.is_default ? `${node.name}（默认）` : node.name,
          disabled: node.is_default === 1,
          children: node.children ? convertToTreeData(node.children) : undefined,
        }))
      setGroupTreeData(convertToTreeData(data.items))
    })
  }, [open, item, type])

  const handleSave = async () => {
    if (!item) return
    setSaving(true)
    try {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('description', description)
      formData.append('tags', JSON.stringify(tags))
      formData.append('search_text', searchText)
      formData.append('file_name', fileName)
      if (selectedGroupId) formData.append('group_id', String(selectedGroupId))
      if (newThumbnail) formData.append('thumbnail', newThumbnail)
      if (newFile) formData.append('file', newFile)
      
      await api.updateResource(item.id, formData)
      message.success('保存成功')
      onSaved?.()
      onClose()
    } catch (e) {
      message.error('保存失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = () => {
    if (!item) return
    Modal.confirm({
      title: '确认删除',
      content: `确定删除资源 "${item.name}" 吗？`,
      okText: '删除',
      okButtonProps: { danger: true },
      onOk: async () => {
        setDeleting(true)
        try {
          await api.deleteResource(item.id)
          message.success('删除成功')
          onSaved?.()
          onClose()
        } catch (e) {
          message.error('删除失败：' + (e instanceof Error ? e.message : '未知错误'))
        } finally {
          setDeleting(false)
        }
      },
    })
  }

  if (!item) return null

  const isInDefaultGroup = groupTreeData.some(node => 
    node.value === item.group_id && node.disabled
  )

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width="clamp(720px, 70%, 2000px)"
      destroyOnClose
      closable={false}
      title={
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 8,
        }}>
          <TreeSelect
            size="small"
            style={{ width: 160 }}
            value={selectedGroupId}
            onChange={setSelectedGroupId}
            treeData={groupTreeData}
            placeholder="切换分组"
            treeDefaultExpandAll
          />
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <Button type="primary" size="small" loading={saving} onClick={handleSave} disabled={isInDefaultGroup}>保存</Button>
            {isInDefaultGroup && <span style={{ color: '#ef4444', fontSize: 11 }}>请切换分组</span>}
            <Button size="small" onClick={onClose}>取消</Button>
            <Button danger size="small" loading={deleting} onClick={handleDelete}>删除</Button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: '42%', flexShrink: 0 }}>
          <div style={{ position: 'relative' }}>
            {newThumbnail ? (
              <img 
                src={URL.createObjectURL(newThumbnail)} 
                alt="new thumbnail"
                style={{ width: '100%', borderRadius: 8, border: '1px solid #e2e8f0' }}
              />
            ) : item.thumbnail_path ? (
              <Image
                src={staticUrl(item.thumbnail_path)}
                width="100%"
                style={{ borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc' }}
              />
            ) : (
              <div style={{
                aspectRatio: '4 / 3', borderRadius: 8, border: '1px dashed #e2e8f0',
                background: '#f8fafc', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: '#cbd5e1', fontSize: 13,
              }}>
                暂无预览图
              </div>
            )}
            <input
              ref={thumbnailInputRef}
              type="file"
              accept="image/png"
              style={{ display: 'none' }}
              onChange={e => {
                const file = e.target.files?.[0]
                if (file) setNewThumbnail(file)
              }}
            />
          </div>
          
          <Button 
            size="small" 
            block 
            style={{ marginTop: 8 }}
            onClick={() => thumbnailInputRef.current?.click()}
          >
            {newThumbnail ? `已选择: ${newThumbnail.name}` : '更新缩略图'}
          </Button>
          
          <Input.TextArea
            placeholder="输入提示词（可选）"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            rows={2}
            style={{ marginTop: 12 }}
          />
          
          <SemanticUnderstand
            resourceId={item.id}
            prompt={prompt}
            onGenerated={setSemanticText}
          />
          
          {semanticText && (
            <div style={{ 
              marginTop: 12, 
              padding: 12, 
              background: '#f8fafc', 
              border: '1px solid #e2e8f0', 
              borderRadius: 8,
              fontSize: 13,
              color: '#334155',
              lineHeight: 1.6,
            }}>
              {semanticText}
              <div style={{ marginTop: 8, textAlign: 'right' }}>
                <Button
                  size="small"
                  type="link"
                  style={{ padding: 0, height: 'auto' }}
                  onClick={() => setDescription(prev => prev ? `${prev}\n${semanticText}` : semanticText)}
                >
                  追加到描述
                </Button>
              </div>
            </div>
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0, overflowY: 'auto', maxHeight: 'calc(100vh - 200px)' }}>
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
          <Field label="关键词">
            <Input value={searchText} onChange={e => setSearchText(e.target.value)} size="small" />
          </Field>
          <Field label="文件名">
            <Input value={fileName} onChange={e => setFileName(e.target.value)} size="small" />
          </Field>

          <SectionHeader title="文件信息" />
          <Field label="缩略图路径">{item.thumbnail_path || emptyCell}</Field>
          <Field label="资源宽度">{item.width ?? emptyCell}</Field>
          <Field label="资源高度">{item.height ?? emptyCell}</Field>
          <Field label="文件路径">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ flex: 1 }}>{newFile ? <span style={{ color: '#059669' }}>{newFile.name}</span> : (item.file_path || emptyCell)}</span>
              <Button size="small" onClick={() => fileInputRef.current?.click()}>
                更新文件
              </Button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              style={{ display: 'none' }}
              onChange={e => {
                const file = e.target.files?.[0]
                if (file) setNewFile(file)
              }}
            />
          </Field>
          <Field label="文件类型">{item.file_type || emptyCell}</Field>
          <Field label="文件大小">{item.file_size ? formatSize(item.file_size) : emptyCell}</Field>
          <Field label="创建时间">{formatDateTime(item.created_at)}</Field>
          <Field label="数据库更新时间">{formatDateTime(item.updated_at)}</Field>
          <Field label="向量库更新时间">{formatDateTime(item.vector_updated_at)}</Field>

          <SectionHeader title="向量文本" />
          <div style={{ 
            padding: 12, 
            background: '#f8fafc', 
            borderRadius: 6, 
            wordBreak: 'break-all', 
            whiteSpace: 'pre-wrap',
            maxHeight: 200,
            overflowY: 'auto',
            fontSize: 12,
            color: '#334155',
          }}>
            {item.vector_text || emptyCell}
          </div>

          {item.raw_data && (
            <>
              <SectionHeader title="原始数据 (raw_data)" />
              <pre style={{
                fontSize: 11,
                fontFamily: 'ui-monospace, monospace',
                color: '#334155',
                margin: 0,
                lineHeight: 1.6,
                background: '#f8fafc',
                padding: 12,
                borderRadius: 6,
                overflow: 'auto',
                maxHeight: 300,
              }}>
                {JSON.stringify(item.raw_data, null, 2)}
              </pre>
            </>
          )}
        </div>
      </div>
    </Drawer>
  )
}

export interface ResourceTableHandle { refresh: () => void }

interface Props {
  type: string
  sourceId: number | null
  groupId: number | null
  handleRef?: React.MutableRefObject<ResourceTableHandle | null>
  extraActions?: React.ReactNode
}

export default function ResourceTable({ type, sourceId, groupId, handleRef, extraActions }: Props) {
  const [items, setItems] = useState<Resource[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [loading, setLoading] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState(false)
  const [detailItem, setDetailItem] = useState<Resource | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const tableRef = useRef<HTMLDivElement>(null)
  const [scrollY, setScrollY] = useState(400)

  useEffect(() => {
    const el = tableRef.current
    if (!el) return
    const update = () => {
      const thead = el.querySelector<HTMLElement>('.ant-table-header')
      const pager = el.querySelector<HTMLElement>('.ant-table-pagination')
      setScrollY(Math.max(100, el.clientHeight - (thead?.offsetHeight ?? 48) - (pager?.offsetHeight ?? 56)))
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
    api.listResources({ type, page, limit: pageSize, source_id: sourceId, group_id: groupId })
      .then(data => {
        if (cancelled) return
        setItems(data.items)
        setTotal(data.total)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [type, page, pageSize, searchMode, refreshKey, sourceId, groupId])

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
      const filters: Record<string, unknown> = { resource_type: type }
      if (sourceId) filters.source_id = sourceId
      if (groupId) filters.group_id = groupId
      const results = await api.vectorSearch({
        query: trimmed,
        type,
        limit: 50,
        filters,
      })
      setItems(results as Resource[])
      setTotal(results.length)
    } catch {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }, [type, sourceId, groupId])

  const refresh = useCallback(() => {
    setSearchMode(false)
    setQuery('')
    setPage(1)
    setRefreshKey(k => k + 1)
  }, [])

  useEffect(() => {
    if (handleRef) handleRef.current = { refresh }
  })

  const columns: ColumnsType<Resource> = [
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
            onClick={e => e.stopPropagation()}
            preview={{ onVisibleChange: (v: boolean) => setIsPreviewing(v) }}
          />
        )
      },
    },
    {
      title: '名称',
      dataIndex: 'name',
      ellipsis: { showTitle: false },
      render: (v: string) => v ? <Tooltip title={v}>{v}</Tooltip> : emptyCell,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: { showTitle: false },
      render: (v: string | null) => v ? <Tooltip title={v}>{v}</Tooltip> : emptyCell,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 160,
      ellipsis: { showTitle: false },
      render: (tags: string[]) => {
        if (!tags?.length) return emptyCell
        const text = tags.join('、')
        return <Tooltip title={text}>{text}</Tooltip>
      },
    },
    {
      title: '关键词',
      dataIndex: 'search_text',
      width: 160,
      ellipsis: { showTitle: false },
      render: (v: string | null) => v ? <Tooltip title={v}>{v}</Tooltip> : emptyCell,
    },
  ]

  const scoreColumn = {
    title: '相似度',
    dataIndex: 'score',
    width: 88,
    render: (v: number) => v ? `${(v * 100).toFixed(1)}%` : '-',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
        padding: '12px 16px', marginBottom: 14, display: 'flex',
        alignItems: 'center', gap: 12, flexShrink: 0,
      }}>
        <Input.Search
          placeholder="向量搜索"
          allowClear
          value={query}
          onChange={e => setQuery(e.target.value)}
          onSearch={handleSearch}
          style={{ width: 280 }}
          prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
          enterButton
        />
        {searchMode && (
          <Button onClick={() => { setQuery(''); handleSearch('') }} size="small">
            返回全量
          </Button>
        )}
        {extraActions && <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>{extraActions}</div>}
      </div>

      <div ref={tableRef} style={{
        flex: 1, minHeight: 0, background: '#fff',
        borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'auto',
      }}>
        <Table
          rowKey="id"
          columns={searchMode ? [scoreColumn, ...columns] : columns}
          dataSource={items}
          loading={loading}
          size="middle"
          scroll={{ y: scrollY }}
          onRow={record => ({
            onClick: () => { if (!isPreviewing) { setDetailItem(record); setDetailOpen(true) } },
            style: { cursor: 'pointer' },
          })}
          pagination={searchMode ? false : {
            current: page, pageSize, total, onChange: setPage,
            showSizeChanger: true, pageSizeOptions: ['10', '20', '50', '100'],
            onShowSizeChange: (_, size) => { setPage(1); setPageSize(size) },
            showQuickJumper: true, showTotal: t => `共 ${t} 条`,
            style: { padding: '12px 20px' },
          }}
          locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无数据</div> }}
        />
      </div>

      <DetailDrawer item={detailItem} open={detailOpen} onClose={() => setDetailOpen(false)} onSaved={refresh} type={type} />
    </div>
  )
}