import { useState, useEffect, useCallback, useRef } from 'react'
import { Table, Input, Button, Drawer, Tooltip, Image, message, Select, Modal, Upload, Tag } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api, staticUrl } from '../api'
import type { Resource } from '../types'
import SemanticUnderstand from './SemanticUnderstand'

const DEFAULT_PAGE_SIZE = 20

const emptyCell = <span style={{ color: '#cbd5e1' }}>-</span>

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}

function formatDateTime(ts: number | null | undefined): string {
  if (!ts) return '-'
  const date = new Date(ts)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

function stripExtension(filename: string): string {
  if (!filename) return ''
  const lastDotIndex = filename.lastIndexOf('.')
  if (lastDotIndex === -1) return filename
  return filename.substring(0, lastDotIndex)
}

function getExtension(filename: string): string {
  if (!filename) return ''
  const lastDotIndex = filename.lastIndexOf('.')
  if (lastDotIndex === -1) return ''
  return filename.substring(lastDotIndex + 1)
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
      <div style={{ width: 100, flexShrink: 0, fontSize: 12, color: '#94a3b8', paddingTop: 2, whiteSpace: 'nowrap' }}>{label}</div>
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
  const [semanticElapsed, setSemanticElapsed] = useState(0)
  
  const [newThumbnail, setNewThumbnail] = useState<File | null>(null)
  const [newFile, setNewFile] = useState<File | null>(null)
  
  const [rawDataString, setRawDataString] = useState('')
  const [rawDataError, setRawDataError] = useState('')
  
  const thumbnailInputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!item) return
    setName(item.name ?? '')
    setDescription(item.description ?? '')
    setTags(item.tags ?? [])
    setSearchText(item.search_text ?? '')
    setFileName(item.file_name ? stripExtension(item.file_name) : '')
    setSelectedGroupId(item.group_id)
    setSemanticText('')
    setSemanticElapsed(0)
    setPrompt('')
    setNewThumbnail(null)
    setNewFile(null)
    setRawDataString(item.raw_data ? JSON.stringify(item.raw_data, null, 2) : '')
    setRawDataError('')
  }, [item])

  const handleSave = async () => {
    if (!item) return
    
    let rawData: Record<string, unknown> | undefined
    if (rawDataString.trim()) {
      try {
        const parsed = JSON.parse(rawDataString)
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          setRawDataError('JSON 必须是对象')
          return
        }
        rawData = parsed
      } catch {
        setRawDataError('JSON 格式错误')
        return
      }
    }
    
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
      if (rawData !== undefined) formData.append('raw_data', JSON.stringify(rawData))
      
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
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <Button type="primary" size="small" loading={saving} onClick={handleSave}>保存</Button>
            <Button size="small" onClick={onClose}>取消</Button>
            <Button danger size="small" loading={deleting} onClick={handleDelete}>删除</Button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: '42%', flexShrink: 0 }}>
          <div style={{
            position: 'relative',
            aspectRatio: '4 / 3',
            borderRadius: 8,
            border: '1px solid #e2e8f0',
            background: '#f8fafc',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            {newThumbnail ? (
              <img 
                src={URL.createObjectURL(newThumbnail)} 
                alt="new thumbnail"
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' as const }}
              />
            ) : item.thumbnail_path ? (
              <Image
                src={staticUrl(item.thumbnail_path)}
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' as const }}
              />
            ) : (
              <span style={{ color: '#cbd5e1', fontSize: 13 }}>暂无预览图</span>
            )}
            <input
              ref={thumbnailInputRef}
              type="file"
              accept="image/png,image/svg+xml,image/jpeg"
              style={{ display: 'none' }}
              onChange={e => {
                const file = e.target.files?.[0]
                if (file) setNewThumbnail(file)
              }}
            />
          </div>

          <Input.TextArea
            placeholder="输入提示词（可选）"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            autoSize={{ minRows: 2 }}
            style={{ marginTop: 12 }}
          />
          
          <SemanticUnderstand
            resourceId={item.id}
            prompt={prompt}
            onGenerated={(text, elapsed) => { setSemanticText(text); setSemanticElapsed(elapsed) }}
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
              <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#94a3b8', fontSize: 12 }}>耗时 {semanticElapsed}s</span>
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
          <Field label="名称">
            <Input.TextArea value={name} onChange={e => setName(e.target.value)} autoSize={{ minRows: 1 }} size="small" />
          </Field>
          <Field label="描述">
            <Input.TextArea
              value={description}
              onChange={e => setDescription(e.target.value)}
              autoSize={{ minRows: 2 }}
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
            <Input.TextArea value={searchText} onChange={e => setSearchText(e.target.value)} autoSize={{ minRows: 1 }} size="small" />
          </Field>
          <Field label="缩略图路径">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ flex: 1 }}>{newThumbnail ? <span style={{ color: '#059669' }}>{newThumbnail.name}</span> : (item.thumbnail_path || emptyCell)}</span>
              <Button 
                size="small" 
                disabled={!item.thumbnail_path || !!newThumbnail}
                onClick={() => {
                  const link = document.createElement('a')
                  link.href = staticUrl(item.thumbnail_path!)
                  const thumbExt = getExtension(item.thumbnail_path!)
                  const downloadName = fileName ? `${fileName}_thumb.${thumbExt}` : (item.thumbnail_path!.split('/').pop() || `thumbnail.${thumbExt}`)
                  link.download = downloadName
                  link.click()
                }}
              >
                下载
              </Button>
              <Button size="small" onClick={() => thumbnailInputRef.current?.click()}>
                更新
              </Button>
            </div>
          </Field>
          <Field label="文件名">
            <Input.TextArea value={fileName} onChange={e => setFileName(e.target.value)} autoSize={{ minRows: 1 }} size="small" />
          </Field>
          <Field label="文件路径">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ flex: 1 }}>{newFile ? <span style={{ color: '#059669' }}>{newFile.name}</span> : (item.file_path || emptyCell)}</span>
              <Button 
                size="small" 
                disabled={!item.file_path || !!newFile}
                onClick={() => {
                  const link = document.createElement('a')
                  link.href = staticUrl(item.file_path!)
                  const ext = getExtension(item.file_path!)
                  const downloadName = fileName ? `${fileName}.${ext}` : item.file_path!.split('/').pop() || 'file'
                  link.download = downloadName
                  link.click()
                }}
              >
                下载
              </Button>
              <Button size="small" onClick={() => fileInputRef.current?.click()}>
                更新
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
          <Field label="业务数据">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <Input.TextArea
                value={rawDataString}
                onChange={e => {
                  const value = e.target.value
                  setRawDataString(value)
                  if (value.trim()) {
                    try {
                      const parsed = JSON.parse(value)
                      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
                        setRawDataError('JSON 必须是对象')
                      } else {
                        setRawDataError('')
                      }
                    } catch {
                      setRawDataError('JSON 格式错误')
                    }
                  } else {
                    setRawDataError('')
                  }
                }}
                autoSize={{ minRows: 3 }}
                size="small"
                style={{ fontFamily: 'ui-monospace, monospace' }}
                status={rawDataError ? 'error' : undefined}
              />
              {rawDataError && <div style={{ color: '#ef4444', fontSize: 10 }}>{rawDataError}</div>}
            </div>
          </Field>

          <SectionHeader title="资源信息" />
          <Field label="ID">{item.id}</Field>
          <Field label="资源宽度">{item.width ?? emptyCell}</Field>
          <Field label="资源高度">{item.height ?? emptyCell}</Field>
          <Field label="向量文本"><div style={{ wordBreak: 'break-all' }}>{item.vector_text || emptyCell}</div></Field>
          <Field label="文件类型">{item.file_type || emptyCell}</Field>
          <Field label="文件大小">{item.file_size ? formatSize(item.file_size) : emptyCell}</Field>
          <Field label="创建时间">{formatDateTime(item.created_at)}</Field>
          <Field label="数据库更新时间">{formatDateTime(item.updated_at)}</Field>
          <Field label="向量库更新时间">{formatDateTime(item.vector_updated_at)}</Field>
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
  selectedRowKeys?: number[]
  onSelectionChange?: (ids: number[]) => void
}

export default function ResourceTable({ type, sourceId, groupId, handleRef, extraActions, selectedRowKeys, onSelectionChange }: Props) {
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
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [tagOptions, setTagOptions] = useState<{ tag: string; count: number }[]>([])
  const tableRef = useRef<HTMLDivElement>(null)
  const [scrollY, setScrollY] = useState(400)

  useEffect(() => {
    const el = tableRef.current
    if (!el) return
    const update = () => {
      const thead = el.querySelector<HTMLElement>('.ant-table-header')
      const pager = el.querySelector<HTMLElement>('.ant-table-pagination')
      setScrollY(Math.max(100, el.clientHeight - (thead?.offsetHeight ?? 48) - (pager?.offsetHeight ?? 56) - 8))
    }
    update()
    const obs = new ResizeObserver(update)
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    setPage(1)
  }, [sourceId, groupId])

  useEffect(() => {
    api.getTags(type, sourceId).then(data => setTagOptions(data.items)).catch(() => {})
  }, [type, sourceId, refreshKey])

  useEffect(() => {
    if (searchMode) return
    let cancelled = false
    setLoading(true)
    api.listResources({ type, page, limit: pageSize, source_id: sourceId, group_id: groupId, tags: selectedTags.length ? selectedTags : undefined })
      .then(data => {
        if (cancelled) return
        setItems(data.items)
        setTotal(data.total)
      })
      .catch(() => message.error('加载失败'))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [type, page, pageSize, searchMode, refreshKey, sourceId, groupId, selectedTags])

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
      const filters: Record<string, unknown> = {}
      if (sourceId) filters.source_id = sourceId
      if (groupId) filters.group_id = groupId
      if (selectedTags.length) filters.tags = selectedTags
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
  }, [type, sourceId, groupId, selectedTags])

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
      title: '分组',
      dataIndex: 'group_path',
      ellipsis: true,
      width: '18%',
      render: (v: string | null) => <div style={{ wordBreak: 'break-all', whiteSpace: 'pre-wrap' }}>{v || emptyCell}</div>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: '18%',
      render: (v: string) => <div style={{ wordBreak: 'break-all' }}>{v || emptyCell}</div>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: '18%',
      render: (v: string | null) => <div style={{ wordBreak: 'break-all' }}>{v || emptyCell}</div>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: '18%',
      render: (tags: string[]) => {
        if (!tags?.length) return emptyCell
        return (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {tags.map((t, i) => <Tag key={i} style={{ margin: 0 }}>{t}</Tag>)}
          </div>
        )
      },
    },
    {
      title: '关键词',
      dataIndex: 'search_text',
      width: '18%',
      render: (v: string | null) => <div style={{ wordBreak: 'break-all' }}>{v || emptyCell}</div>,
    },
  ]

  const scoreColumn = {
    title: '相似度',
    dataIndex: 'score',
    width: 80,
    render: (v: number) => v ? `${(v * 100).toFixed(1)}%` : '-',
  }

  const vectorTextColumn = {
    title: '向量文本',
    dataIndex: 'vector_text',
    width: 200,
    render: (v: string | null) => v
      ? <div style={{ wordBreak: 'break-all', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{v}</div>
      : '-',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, minWidth: 0, overflow: 'hidden' }}>
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
        <Select
          mode="multiple"
          showSearch
          maxTagCount={0}
          style={{ width: 160 }}
          placeholder="标签筛选"
          value={selectedTags}
          onChange={(vals: string[]) => {
            setSelectedTags(vals)
            if (searchMode && query.trim()) {
              handleSearch(query)
            }
          }}
          options={tagOptions.map(t => ({ label: `${t.tag} (${t.count})`, value: t.tag }))}
          filterOption={(input, option) =>
            (option?.value as string)?.toLowerCase().includes(input.toLowerCase())
          }
          allowClear
        />
        {searchMode && (
          <Button onClick={() => { setQuery(''); handleSearch('') }} size="small">
            返回全量
          </Button>
        )}
        <div style={{ display: 'flex', gap: 16, marginLeft: 12, color: '#64748b', fontSize: 13 }}>
          <span>来源ID: <span style={{ color: '#1e293b', fontWeight: 500 }}>{sourceId ?? 'null'}</span></span>
          <span>分组ID: <span style={{ color: '#1e293b', fontWeight: 500 }}>{groupId ?? 'null'}</span></span>
          <span>数据量: <span style={{ color: '#1e293b', fontWeight: 500 }}>{total}</span></span>
        </div>
        {extraActions && <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>{extraActions}</div>}
      </div>

      {selectedTags.length > 0 && (
        <div style={{
          display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center',
          padding: '0 4px', marginBottom: 10, flexShrink: 0,
        }}>
          <span style={{ fontSize: 12, color: '#94a3b8', marginRight: 4 }}>已选标签:</span>
          {selectedTags.map(tag => (
            <Tag
              key={tag}
              closable
              onClose={e => {
                e.preventDefault()
                const next = selectedTags.filter(t => t !== tag)
                setSelectedTags(next)
                if (searchMode && query.trim()) {
                  handleSearch(query)
                }
              }}
              style={{ margin: 0, borderRadius: 4 }}
            >
              {tag}
            </Tag>
          ))}
        </div>
      )}

      <div ref={tableRef} style={{
        flex: 1, minHeight: 0, minWidth: 0, background: '#fff',
        borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden',
      }}>
        <style>{`
          .custom-table .ant-table-thead > tr > th:nth-child(1),
          .custom-table .ant-table-tbody > tr > td:nth-child(1) {
            width: 48px !important;
            min-width: 48px !important;
            max-width: 48px !important;
          }
          .custom-table .ant-table-thead > tr > th:nth-child(2),
          .custom-table .ant-table-tbody > tr > td:nth-child(2) {
            width: 80px !important;
            min-width: 80px !important;
            max-width: 80px !important;
          }
          .custom-table .ant-table-thead > tr > th:nth-child(n+3),
          .custom-table .ant-table-tbody > tr > td:nth-child(n+3) {
            width: calc((100% - 128px) / 5) !important;
          }
          .custom-table.search-mode .ant-table-thead > tr > th:nth-child(1),
          .custom-table.search-mode .ant-table-tbody > tr > td:nth-child(1) {
            width: 48px !important;
            min-width: 48px !important;
            max-width: 48px !important;
          }
          .custom-table.search-mode .ant-table-thead > tr > th:nth-child(2),
          .custom-table.search-mode .ant-table-tbody > tr > td:nth-child(2) {
            width: 80px !important;
            min-width: 80px !important;
            max-width: 80px !important;
            background: #e6f4ff !important;
          }
          .custom-table.search-mode .ant-table-thead > tr > th:nth-child(3),
          .custom-table.search-mode .ant-table-tbody > tr > td:nth-child(3) {
            width: 200px !important;
            min-width: 200px !important;
            max-width: 200px !important;
            background: #e6f4ff !important;
          }
          .custom-table.search-mode .ant-table-thead > tr > th:nth-child(4),
          .custom-table.search-mode .ant-table-tbody > tr > td:nth-child(4) {
            width: 80px !important;
            min-width: 80px !important;
            max-width: 80px !important;
          }
          .custom-table.search-mode .ant-table-thead > tr > th:nth-child(n+5),
          .custom-table.search-mode .ant-table-tbody > tr > td:nth-child(n+5) {
            width: calc((100% - 408px) / 5) !important;
          }
        `}</style>
        <Table
          className={`custom-table${searchMode ? ' search-mode' : ''}`}
          rowKey="id"
          columns={searchMode ? [scoreColumn, vectorTextColumn, ...columns] : columns}
          dataSource={items}
          loading={loading}
          size="middle"
          tableLayout="fixed"
          scroll={{ y: scrollY }}
          rowSelection={selectedRowKeys !== undefined ? {
            selectedRowKeys,
            onChange: (keys) => onSelectionChange?.(keys as number[]),
            columnWidth: 48,
          } : undefined}
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