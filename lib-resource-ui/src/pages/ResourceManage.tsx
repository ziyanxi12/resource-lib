import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Select, TreeSelect, message, Modal, Input, Spin, Dropdown, Upload, Progress, Alert, Tooltip } from 'antd'
import { UploadOutlined, SyncOutlined, DeleteOutlined, PlusOutlined, EditOutlined, UndoOutlined, SettingOutlined, SwapOutlined, ImportOutlined, CloseOutlined, DownloadOutlined, FileTextOutlined } from '@ant-design/icons'
import JSZip from 'jszip'
import ResourceTable, { type ResourceTableHandle } from '../components/ResourceTable'
import GroupTree, { type GroupTreeHandle } from '../components/GroupTree'
import OperationLogModal from '../components/OperationLogModal'
import { api, Source, GroupNode } from '../api'

const RESOURCE_TYPE_MAP: Record<string, number> = {
  component: 1,
  icon: 3,
  illus: 4,
  image: 5,
  file: 6,
}

export default function ResourceManage() {
  const { type = 'component' } = useParams<{ type: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const sourceIdParam = searchParams.get('sourceId')
  const groupIdParam = searchParams.get('groupId')
  const tableRef = useRef<ResourceTableHandle | null>(null)
  const groupTreeRef = useRef<GroupTreeHandle | null>(null)
  const [groupId, setGroupId] = useState<number | null>(null)
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [createSourceModalOpen, setCreateSourceModalOpen] = useState(false)
  const [newSourceName, setNewSourceName] = useState('')
  const [creatingSource, setCreatingSource] = useState(false)
  const [editSourceModalOpen, setEditSourceModalOpen] = useState(false)
  const [editSourceName, setEditSourceName] = useState('')
  const [updatingSource, setUpdatingSource] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)
  const [trashModalOpen, setTrashModalOpen] = useState(false)
  const [trashSources, setTrashSources] = useState<Source[]>([])
  const [deleteSourceModalOpen, setDeleteSourceModalOpen] = useState(false)
  const [deletingSource, setDeletingSource] = useState(false)
  const [restoringSource, setRestoringSource] = useState(false)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [moveModalOpen, setMoveModalOpen] = useState(false)
  const [moveTargetGroupId, setMoveTargetGroupId] = useState<number | null>(null)
  const [moving, setMoving] = useState(false)
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importProgress, setImportProgress] = useState(0)
  const [importPhase, setImportPhase] = useState<'uploading' | 'processing' | null>(null)
  const [importTaskId, setImportTaskId] = useState<string | null>(null)
  const [importTaskStatus, setImportTaskStatus] = useState<{
    status: string
    phase: number
    phase_label: string
    groups_created: number
    resources_created: number
    errors: Array<{ group?: string; label?: string; name?: string; reason: string }>
    message: string
  } | null>(null)
  const xhrRef = useRef<XMLHttpRequest | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const importTaskIdRef = useRef<string | null>(null)
  const [logModalOpen, setLogModalOpen] = useState(false)

  useEffect(() => {
    setPageLoading(true)
    api.getSources()
      .then(data => {
        const typeNum = RESOURCE_TYPE_MAP[type]
        const filtered = data.items.filter(s => s.resource_type === typeNum)
        setSources(filtered)
        
        if (filtered.length > 0) {
          if (sourceIdParam) {
            const s = filtered.find(x => x.id === Number(sourceIdParam))
            if (s) {
              setSourceId(s.id)
            } else {
              setSourceId(filtered[0].id)
            }
          } else {
            setSourceId(filtered[0].id)
          }
        } else {
          setSourceId(null)
        }
      })
      .catch(() => message.error('加载来源失败'))
      .finally(() => setPageLoading(false))
  }, [type])

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  // 页面加载时恢复未完成的导入任务
  useEffect(() => {
    let stale = false

    // 切换来源时：先彻底清除导入状态
    stopPolling()
    importTaskIdRef.current = null
    setImporting(false)
    setImportProgress(0)
    setImportPhase(null)
    setImportTaskId(null)
    setImportTaskStatus(null)

    if (!sourceId) return

    // 检查是否有未完成的导入任务需要恢复
    const saved = localStorage.getItem('import_task')
    if (!saved) return
    let parsed: { task_id: string; source_id: number; type: string }
    try { parsed = JSON.parse(saved) } catch { localStorage.removeItem('import_task'); return }
    if (parsed.type !== type || parsed.source_id !== sourceId) return

    // 匹配：恢复进度
    setImportPhase('processing')
    setImportTaskId(parsed.task_id)
    api.getImportTaskStatus(parsed.task_id).then(status => {
      if (stale) return
      setImportTaskStatus(status)
      if (status.status === 'pending' || status.status === 'running') {
        startPolling(parsed.task_id)
      } else {
        if (status.status === 'success') {
          message.success(`导入完成：${status.groups_created} 个分组，${status.resources_created} 个资源`)
          groupTreeRef.current?.refresh()
          tableRef.current?.refresh()
        } else if (status.status === 'failed') {
          message.error(status.message || '导入失败')
        } else if (status.status === 'cancelled') {
          message.info('导入已取消')
        }
        setImportPhase(null)
        setImportTaskId(null)
        setImportTaskStatus(null)
        localStorage.removeItem('import_task')
      }
    }).catch(() => {
      if (stale) return
      localStorage.removeItem('import_task')
      setImportPhase(null)
      setImportTaskId(null)
    })

    return () => { stale = true }
  }, [type, sourceId])

  const findGroup = (nodes: GroupNode[], targetId: number): GroupNode | null => {
    for (const node of nodes) {
      if (node.id === targetId) return node
      if (node.children) {
        const found = findGroup(node.children, targetId)
        if (found) return found
      }
    }
    return null
  }

  useEffect(() => {
    if (!sourceId) {
      setGroupId(null)
      setGroups([])
      return
    }
    
    api.getGroups(type, sourceId, false)
      .then(data => {
        setGroups(data.items)
        
        if (data.items.length > 0) {
          if (groupIdParam) {
            const id = Number(groupIdParam)
            const group = findGroup(data.items, id)
            if (group) {
              setGroupId(id)
            } else {
              const defaultGroup = data.items.find(item => item.is_default === 1)
              setGroupId(defaultGroup ? defaultGroup.id : data.items[0].id)
            }
          } else {
            const defaultGroup = data.items.find(item => item.is_default === 1)
            setGroupId(defaultGroup ? defaultGroup.id : data.items[0].id)
          }
        } else {
          setGroupId(null)
        }
      })
      .catch(() => {
        setGroupId(null)
        setGroups([])
      })
  }, [type, sourceId])

  useEffect(() => {
    if (sourceId && groupId) {
      const currentSourceId = searchParams.get('sourceId')
      const currentGroupId = searchParams.get('groupId')
      
      if (currentSourceId !== String(sourceId) || currentGroupId !== String(groupId)) {
        setSearchParams({ sourceId: String(sourceId), groupId: String(groupId) }, { replace: true })
      }
    } else if (sourceId) {
      const currentSourceId = searchParams.get('sourceId')
      if (currentSourceId !== String(sourceId)) {
        setSearchParams({ sourceId: String(sourceId) }, { replace: true })
      }
    }
  }, [sourceId, groupId, setSearchParams, searchParams])

  const handleSyncVectors = async () => {
    setSyncing(true)
    try {
      const r = await api.syncVectors(type, sourceId)
      message.success(r.message)
      tableRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '向量同步失败')
    } finally {
      setSyncing(false)
    }
  }

  const handleCreateSource = async () => {
    if (!newSourceName.trim()) {
      message.warning('请输入来源名称')
      return
    }
    
    setCreatingSource(true)
    try {
      const source = await api.createSource({
        name: newSourceName.trim(),
        type: type,
        is_sync_source: 0,
        is_active: 1,
      })
      
      await api.createGroup({
        type: type,
        source_id: source.id,
        name: '默认分组',
        parent_id: null,
      })
      
      message.success('创建成功')
      setCreateSourceModalOpen(false)
      setNewSourceName('')
      
      const data = await api.getSources()
      const typeNum = RESOURCE_TYPE_MAP[type]
      const filtered = data.items.filter(s => s.resource_type === typeNum)
      setSources(filtered)
      setSourceId(source.id)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '创建失败')
    } finally {
      setCreatingSource(false)
    }
  }

  const handleEditSource = async () => {
    if (!editSourceName.trim()) {
      message.warning('请输入来源名称')
      return
    }
    
    setUpdatingSource(true)
    try {
      await api.updateSource(sourceId!, { name: editSourceName.trim() })
      message.success('修改成功')
      setEditSourceModalOpen(false)
      
      const data = await api.getSources()
      const typeNum = RESOURCE_TYPE_MAP[type]
      const filtered = data.items.filter(s => s.resource_type === typeNum)
      setSources(filtered)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '修改失败')
    } finally {
      setUpdatingSource(false)
    }
  }

  const handleDeleteSource = async () => {
    setDeletingSource(true)
    try {
      await api.deleteSource(sourceId!)
      message.success('已移入回收站')
      setDeleteSourceModalOpen(false)
      setSourceId(null)
      
      const data = await api.getSources()
      const typeNum = RESOURCE_TYPE_MAP[type]
      const filtered = data.items.filter(s => s.resource_type === typeNum)
      setSources(filtered)
      if (filtered.length > 0) {
        setSourceId(filtered[0].id)
      }
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    } finally {
      setDeletingSource(false)
    }
  }

  const loadTrashSources = async () => {
    try {
      const data = await api.getTrashSources({ type })
      setTrashSources(data.items)
    } catch (e) {
      message.error('加载回收站失败')
    }
  }

  const handleRestoreSource = async (id: number) => {
    setRestoringSource(true)
    try {
      await api.restoreSource(id)
      message.success('恢复成功')
      
      const [normalData, trashData] = await Promise.all([
        api.getSources(),
        api.getTrashSources({ type })
      ])
      
      const typeNum = RESOURCE_TYPE_MAP[type]
      const filtered = normalData.items.filter(s => s.resource_type === typeNum)
      setSources(filtered)
      setTrashSources(trashData.items)
      
      if (!sourceId && filtered.length > 0) {
        setSourceId(filtered[0].id)
      }
    } catch (e) {
      message.error(e instanceof Error ? e.message : '恢复失败')
    } finally {
      setRestoringSource(false)
    }
  }

  useEffect(() => {
    loadTrashSources()
  }, [type])

  const handleBatchDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除选中的 ${selectedIds.length} 项资源？`,
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.batchDeleteResources(selectedIds, type)
          message.success('删除成功')
          setSelectedIds([])
          tableRef.current?.refresh()
          groupTreeRef.current?.refresh()
        } catch (e) {
          message.error(e instanceof Error ? e.message : '删除失败')
        }
      },
    })
  }

  const handleBatchMove = async () => {
    if (!moveTargetGroupId) {
      message.warning('请选择目标分组')
      return
    }
    setMoving(true)
    try {
      await api.batchMoveResources(selectedIds, moveTargetGroupId, type)
      message.success('移动成功')
      setSelectedIds([])
      setMoveModalOpen(false)
      setMoveTargetGroupId(null)
      tableRef.current?.refresh()
      groupTreeRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '移动失败')
    } finally {
      setMoving(false)
    }
  }

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const startPolling = (taskId: string) => {
    stopPolling()
    importTaskIdRef.current = taskId
    pollRef.current = setInterval(async () => {
      try {
        const status = await api.getImportTaskStatus(taskId)
        if (importTaskIdRef.current !== taskId) return
        setImportTaskStatus(status)
        if (status.status === 'pending' || status.status === 'running') return
        stopPolling()
        importTaskIdRef.current = null
        if (status.status === 'success') {
          message.success(`导入完成：${status.groups_created} 个分组，${status.resources_created} 个资源`)
          groupTreeRef.current?.refresh()
          tableRef.current?.refresh()
        } else if (status.status === 'failed') {
          message.error(status.message || '导入失败')
        } else if (status.status === 'cancelled') {
          message.info('导入已取消')
        }
        setImporting(false)
        setImportPhase(null)
        setImportTaskId(null)
        setImportTaskStatus(null)
        setImportFile(null)
        localStorage.removeItem('import_task')
      } catch {
        // 轮询单次失败不中断，继续下一轮
      }
    }, 2000)
  }

  const handleFullImport = async () => {
    if (!importFile || !sourceId) return
    setImporting(true)
    setImportProgress(0)
    setImportPhase('uploading')
    setImportTaskStatus(null)
    setImportTaskId(null)
    try {
      // 阶段 1：上传 ZIP
      const res = await api.fullBatchImport(sourceId, type, importFile, {
        onProgress: setImportProgress,
        getXhr: (xhr) => { xhrRef.current = xhr },
      })
      // 上传完成，切换到处理阶段，关闭 Modal，进度转移到来源卡片
      setImportPhase('processing')
      setImportTaskId(res.task_id)
      setImportModalOpen(false)
      localStorage.setItem('import_task', JSON.stringify({
        task_id: res.task_id,
        source_id: sourceId,
        type,
      }))

      // 阶段 2：轮询服务端处理进度
      startPolling(res.task_id)
    } catch (e) {
      const msg = e instanceof Error ? e.message : '导入失败'
      if (msg !== '已取消') message.error(msg)
      setImporting(false)
      setImportPhase(null)
    } finally {
      xhrRef.current = null
    }
  }

  const closeImportModal = () => {
    // 上传阶段关闭：中断 XHR + 全部清理
    if (importPhase === 'uploading' && xhrRef.current) {
      xhrRef.current.abort()
    }
    // 处理阶段关闭：只关 Modal，进度继续在来源卡片展示（不停轮询）
    if (importPhase === 'processing') {
      setImportModalOpen(false)
      return
    }
    // 空闲状态：清理
    stopPolling()
    setImportModalOpen(false)
    setImportFile(null)
    setImportProgress(0)
    setImportPhase(null)
    setImportTaskId(null)
    setImportTaskStatus(null)
    setImporting(false)
  }

  const downloadImportTemplate = async () => {
    const zip = new JSZip()

    const config = {
      group: [
        {
          label: '示例分组',
          data: [
            {
              name: '示例资源',
              file_name: 'example.svg',
              file_path: 'data/example.svg',
              thumbnail_path: 'image/example.png',
              description: '示例描述',
              tags: ['示例'],
              search_text: '关键词',
              raw_data: {},
            },
          ],
          children: [
            { label: '子分组', data: [] },
          ],
        },
      ],
    }

    zip.file('config.json', JSON.stringify(config, null, 2))

    const readme = `# 全量批量导入 ZIP 模板说明

## 文件结构
\`\`\`
├── config.json      # 配置文件（必填，含分组树）
├── image/           # 缩略图目录
│   └── example.png
└── data/            # 资源文件目录
    └── example.svg
\`\`\`

## config.json 格式

config.json 的顶层是 \`group\` 数组，每个元素是一个分组节点，支持递归 \`children\` 嵌套：

\`\`\`json
{
  "group": [
    {
      "label": "分组名称",
      "data": [ { ...资源项... } ],
      "children": [
        { "label": "子分组", "data": [] }
      ]
    }
  ]
}
\`\`\`

### 分组节点字段
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| label | string | 是 | 分组名称 |
| data | array | 否 | 该分组下的资源列表 |
| children | array | 否 | 子分组列表（递归结构） |

## 分组说明

1. **顶层分组放置规则**：\`group\` 数组中的每个分组，都会作为该来源下"默认分组"的子分组创建。
   - "默认分组"是系统自动创建的根分组（\`is_default=1\`）。
   - 已存在则自动复用，不存在则自动创建。
2. **不去重，直接创建**：每次导入都会创建全新的分组和全新的资源，不会与已有同名分组合并，也不会覆盖已有数据。
   - 多次导入同一 ZIP 会产生重复的分组和资源。
3. **递归嵌套**：\`children\` 中的子分组会挂在对应父分组下，层级无限制。

### data 字段（资源列表）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 资源名称 |
| file_name | string | 否 | 展示文件名（用于前端显示） |
| file_path | string | 否 | 文件在ZIP中的相对路径 |
| thumbnail_path | string | 否 | 缩略图在ZIP中的相对路径（支持 PNG/SVG/JPEG 格式，宽高自动读取），可选 |
| description | string | 否 | 资源描述 |
| tags | array | 否 | 标签数组 |
| search_text | string | 否 | 搜索关键词 |
| raw_data | object | 否 | 自定义元数据 |

## 注意事项
1. 导入会在选中来源下递归创建分组树及资源
2. 顶层分组会自动放在"默认分组"下，默认分组已存在则复用，否则自动创建
3. 导入不去重，直接创建新分组和新数据，不会与已有同名分组合并，也不会覆盖已有数据
4. file_path 指向的文件必须存在于 ZIP 包内
5. thumbnail_path 指向的缩略图也必须存在于 ZIP 包内
`

    zip.file('README.md', readme)

    // 1x1 像素 PNG
    const minPNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    const pngBlob = await fetch(minPNG).then(r => r.blob())
    zip.file('image/example.png', pngBlob)

    // 最小 SVG
    const minSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><rect width="24" height="24" fill="#ccc"/></svg>'
    zip.file('data/example.svg', minSVG)

    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${type}_import_template.zip`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (pageLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        flex: 1,
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }
  
  return (
    <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0, minWidth: 0, overflow: 'hidden' }}>
      {/* 左侧栏：来源选择 + 分组树 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>
        <div style={{
          background: '#fff', borderRadius: 8, padding: 12,
          border: '1px solid #e2e8f0',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>
              来源
            </div>
            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => setCreateSourceModalOpen(true)}
              />
              <Dropdown
                menu={{
                  items: [
                    { key: 'edit', label: '编辑名称', icon: <EditOutlined /> },
                    { key: 'delete', label: '删除来源', icon: <DeleteOutlined />, danger: true },
                    { key: 'trash', label: '回收站', icon: <UndoOutlined /> },
                    { type: 'divider' as const },
                    { key: 'sync', label: '向量同步', icon: <SyncOutlined spin={syncing} /> },
                    { key: 'import', label: '全量批量导入', icon: <ImportOutlined /> },
                    { type: 'divider' as const },
                    { key: 'log', label: '操作日志', icon: <FileTextOutlined /> },
                  ],
                  onClick: ({ key }) => {
                    if (key === 'edit') {
                      const source = sources.find(s => s.id === sourceId)
                      if (source) {
                        setEditSourceName(source.name)
                        setEditSourceModalOpen(true)
                      }
                    }
                    if (key === 'delete') setDeleteSourceModalOpen(true)
                    if (key === 'trash') { loadTrashSources(); setTrashModalOpen(true) }
                    if (key === 'sync') handleSyncVectors()
                    if (key === 'import') {
                      setImportFile(null)
                      setImportProgress(0)
                      setImportModalOpen(true)
                    }
                    if (key === 'log') setLogModalOpen(true)
                  },
                }}
                trigger={['click']}
                disabled={!sourceId}
              >
                <Button size="small" icon={<SettingOutlined />} disabled={!sourceId} />
              </Dropdown>
            </div>
          </div>

          <Tooltip
            title={sourceId ? (() => {
              const src = sources.find(s => s.id === sourceId)
              if (!src) return ''
              const parts: string[] = []
              if (src.created_by) parts.push(`创建者: ${src.created_by}`)
              if (src.updated_by) parts.push(`修改者: ${src.updated_by}`)
              return parts.join('\n')
            })() : ''}
            placement="bottom"
            overlayInnerStyle={{ whiteSpace: 'pre-wrap', fontSize: 12 }}
          >
            <Select
              value={sourceId}
              onChange={setSourceId}
              placeholder="选择来源"
              style={{ width: '100%' }}
              optionRender={(option: any) => (
                <span style={{ 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  display: 'block'
                }}>
                  {option?.label}
                </span>
              )}
              options={sources.map(s => ({ value: s.id, label: s.name }))}
            />
          </Tooltip>

          {importTaskId && importPhase === 'processing' && (
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
              {[1, 2, 3].map((step) => {
                const isError = importTaskStatus?.status === 'failed' || importTaskStatus?.status === 'cancelled'
                const bg = importTaskStatus && importTaskStatus.phase > step
                  ? '#52c41a'
                  : importTaskStatus && importTaskStatus.phase === step
                    ? (isError ? '#ff4d4f' : '#1677ff')
                    : '#e2e8f0'
                return (
                  <div key={step} style={{ flex: 1, height: 4, borderRadius: 2, background: bg, transition: 'background 0.3s' }} />
                )
              })}
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                onClick={() => { if (importTaskId) api.cancelImportTask(importTaskId).catch(() => {}) }}
              />
            </div>
          )}
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <GroupTree
            ref={groupTreeRef}
            type={type}
            selectedId={groupId}
            onSelect={setGroupId}
            sourceId={sourceId}
          />
        </div>
      </div>

      {/* 右侧：表格 */}
      <div style={{ flex: 4, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <ResourceTable
          type={type}
          sourceId={sourceId}
          groupId={groupId}
          handleRef={tableRef}
          selectedRowKeys={selectedIds}
          onSelectionChange={setSelectedIds}
          extraActions={
            <>
              {selectedIds.length > 0 && (
                <Dropdown
                  menu={{
                    items: [
                      { key: 'move', label: '移动', icon: <SwapOutlined /> },
                      { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
                    ],
                    onClick: ({ key }) => {
                      if (key === 'move') {
                        setMoveTargetGroupId(null)
                        setMoveModalOpen(true)
                      }
                      if (key === 'delete') handleBatchDelete()
                    },
                  }}
                  trigger={['click']}
                >
                  <Button icon={<EditOutlined />}>批量编辑 ({selectedIds.length})</Button>
                </Dropdown>
              )}
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={() => {
                  if (!sourceId) return
                  const url = groupId 
                    ? `/${type}/upload?sourceId=${sourceId}&groupId=${groupId}`
                    : `/${type}/upload?sourceId=${sourceId}`
                  navigate(url)
                }}
                disabled={!sourceId}
              >
                批量上传
              </Button>
            </>
          }
        />
      </div>

      <Modal
        open={createSourceModalOpen}
        title="新增来源"
        onCancel={() => {
          setCreateSourceModalOpen(false)
          setNewSourceName('')
        }}
        onOk={handleCreateSource}
        okText="创建"
        okButtonProps={{ loading: creatingSource }}
      >
        <Input
          placeholder="请输入来源名称"
          value={newSourceName}
          onChange={e => setNewSourceName(e.target.value)}
          autoFocus
        />
      </Modal>

      <Modal
        open={editSourceModalOpen}
        title="编辑来源"
        onCancel={() => {
          setEditSourceModalOpen(false)
          setEditSourceName('')
        }}
        onOk={handleEditSource}
        okText="保存"
        okButtonProps={{ loading: updatingSource }}
      >
        <Input
          placeholder="请输入来源名称"
          value={editSourceName}
          onChange={e => setEditSourceName(e.target.value)}
          autoFocus
        />
      </Modal>

      <Modal
        open={deleteSourceModalOpen}
        title="删除来源"
        onCancel={() => setDeleteSourceModalOpen(false)}
        onOk={handleDeleteSource}
        okText="删除"
        okButtonProps={{ danger: true, loading: deletingSource }}
      >
        <p>确定删除当前来源吗？</p>
        <p style={{ color: '#64748b', fontSize: 13 }}>
          该来源及其下的所有资源将移入回收站，可以随时恢复。
        </p>
      </Modal>

      <Modal
        open={trashModalOpen}
        title="回收站"
        onCancel={() => setTrashModalOpen(false)}
        footer={<Button onClick={() => setTrashModalOpen(false)}>关闭</Button>}
      >
        <div style={{ maxHeight: 300, overflowY: 'auto' }}>
          {trashSources.length === 0 ? (
            <div style={{ color: '#94a3b8', fontSize: 12, padding: '8px 0', textAlign: 'center' }}>
              回收站为空
            </div>
          ) : (
            trashSources.map(s => (
              <div
                key={s.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '6px 8px',
                  background: '#f8fafc',
                  borderRadius: 4,
                  marginBottom: 4,
                }}
              >
                <span style={{ fontSize: 13, color: '#475569' }}>{s.name}</span>
                <Button
                  size="small"
                  type="link"
                  icon={<UndoOutlined />}
                  loading={restoringSource}
                  onClick={() => handleRestoreSource(s.id)}
                  style={{ padding: 0, height: 'auto' }}
                />
              </div>
            ))
          )}
        </div>
      </Modal>

      <Modal
        open={moveModalOpen}
        title={`移动 ${selectedIds.length} 项到分组`}
        onCancel={() => { setMoveModalOpen(false); setMoveTargetGroupId(null) }}
        onOk={handleBatchMove}
        okText="确定"
        okButtonProps={{ loading: moving }}
        cancelText="取消"
      >
        <TreeSelect
          value={moveTargetGroupId}
          onChange={setMoveTargetGroupId}
          placeholder="选择目标分组"
          style={{ width: '100%' }}
          treeDefaultExpandAll
          treeData={groups.map(function convert(g: GroupNode): any {
            return {
              value: g.id,
              title: g.name,
              children: (g.children || []).map(convert),
            }
          })}
        />
      </Modal>

      <Modal
        open={importModalOpen}
        title="全量批量导入"
        onCancel={closeImportModal}
        footer={[
          <Button key="close" onClick={closeImportModal} danger={importing}>
            {importPhase === 'uploading' ? '取消上传' : '关闭'}
          </Button>,
          <Button
            key="template"
            icon={<DownloadOutlined />}
            onClick={downloadImportTemplate}
            disabled={importing}
          >
            下载模板
          </Button>,
          <Button
            key="upload"
            type="primary"
            loading={importing}
            disabled={!importFile || importing}
            onClick={handleFullImport}
            icon={<ImportOutlined />}
          >
            开始导入
          </Button>,
        ]}
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="ZIP 包需包含 config.json（含 group 分组树）及引用的资源文件和缩略图"
        />
        <Upload.Dragger
          accept=".zip"
          maxCount={1}
          beforeUpload={(file) => {
            setImportFile(file)
            return false
          }}
          onRemove={() => { setImportFile(null) }}
          fileList={importFile ? [{ uid: '-1', name: importFile.name, status: 'done' as const }] : []}
          disabled={importing}
        >
          <p style={{ margin: '8px 0' }}><ImportOutlined style={{ fontSize: 32, color: '#1677ff' }} /></p>
          <p style={{ margin: 0 }}>点击或拖拽 ZIP 文件到此处</p>
          <p style={{ margin: '4px 0 0', color: '#999', fontSize: 12 }}>仅支持 .zip 格式</p>
        </Upload.Dragger>

        {importPhase === 'uploading' && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={importProgress} status="active" />
            <div style={{ textAlign: 'center', color: '#999', fontSize: 12, marginTop: 4 }}>
              上传中... {importProgress}%
            </div>
          </div>
        )}
      </Modal>

      <OperationLogModal sourceId={sourceId} open={logModalOpen} onClose={() => setLogModalOpen(false)} />
    </div>
  )
}