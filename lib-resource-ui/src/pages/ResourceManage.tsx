import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Select, message, Modal, Input, Spin } from 'antd'
import { UploadOutlined, SyncOutlined, DeleteOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons'
import ResourceTable, { type ResourceTableHandle } from '../components/ResourceTable'
import GroupTree from '../components/GroupTree'
import { api, Source, GroupNode } from '../api'

const RESOURCE_TYPE_MAP: Record<string, number> = {
  component: 1,
  template: 2,
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
  const [groupId, setGroupId] = useState<number | null>(null)
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [clearModalOpen, setClearModalOpen] = useState(false)
  const [clearModalCount, setClearModalCount] = useState<number | null>(null)
  const [clearModalLoading, setClearModalLoading] = useState(false)
  const [createSourceModalOpen, setCreateSourceModalOpen] = useState(false)
  const [newSourceName, setNewSourceName] = useState('')
  const [creatingSource, setCreatingSource] = useState(false)
  const [editSourceModalOpen, setEditSourceModalOpen] = useState(false)
  const [editSourceName, setEditSourceName] = useState('')
  const [updatingSource, setUpdatingSource] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)

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

  const handleClearClick = async () => {
    setClearModalLoading(true)
    setClearModalOpen(true)
    try {
      const data = await api.listResources({ 
        type, 
        source_id: sourceId, 
        group_id: groupId, 
        page: 1, 
        limit: 1 
      })
      setClearModalCount(data.total)
    } catch {
      setClearModalCount(null)
    } finally {
      setClearModalLoading(false)
    }
  }

  const handleClear = async () => {
    setClearing(true)
    try {
      const r = await api.clearResources(type, sourceId, groupId)
      message.success(`已删除 ${r.deleted} 条数据`)
      setClearModalOpen(false)
      tableRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '清空失败')
    } finally {
      setClearing(false)
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

  const isInDefaultGroup = groups.some(g => g.id === groupId && g.is_default === 1)
  
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
    <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
      {/* 左侧栏：来源选择 + 分组树 */}
      <div style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{
          background: '#fff', borderRadius: 8, padding: 12,
          border: '1px solid #e2e8f0',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>
              来源
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => setCreateSourceModalOpen(true)}
              />
              <Button
                size="small"
                icon={<EditOutlined />}
                disabled={!sourceId}
                onClick={() => {
                  const source = sources.find(s => s.id === sourceId)
                  if (source) {
                    setEditSourceName(source.name)
                    setEditSourceModalOpen(true)
                  }
                }}
              />
              <Button
                size="small"
                icon={<SyncOutlined spin={syncing} />}
                loading={syncing}
                onClick={handleSyncVectors}
                disabled={!sourceId}
              >
                向量同步
              </Button>
            </div>
          </div>
          <Select
            value={sourceId}
            onChange={setSourceId}
            options={sources.map(s => ({ value: s.id, label: s.name }))}
            placeholder="选择来源"
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <GroupTree
            type={type}
            selectedId={groupId}
            onSelect={setGroupId}
            sourceId={sourceId}
            width={280}
          />
        </div>
      </div>

      {/* 右侧：表格 */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <ResourceTable
          type={type}
          sourceId={sourceId}
          groupId={groupId}
          handleRef={tableRef}
          extraActions={
            <>
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
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleClearClick}
                disabled={!sourceId}
              >
                清空数据
              </Button>
            </>
          }
        />
      </div>

      <Modal
        open={clearModalOpen}
        title="确认清空"
        onCancel={() => setClearModalOpen(false)}
        onOk={handleClear}
        okText="确认清空"
        okButtonProps={{ danger: true, loading: clearing }}
      >
        {clearModalLoading ? (
          <p style={{ color: '#64748b' }}>正在统计数据...</p>
        ) : (
          <p>确定清空当前筛选条件下的所有数据吗？</p>
        )}
        {clearModalCount !== null && !clearModalLoading && (
          <p style={{ fontWeight: 500 }}>
            即将删除 <span style={{ color: '#ef4444' }}>{clearModalCount}</span> 条数据
          </p>
        )}
        <p style={{ color: '#64748b', fontSize: 12 }}>
          类型：{type}
          {sourceId && ` | 来源ID: ${sourceId}`}
          {groupId && ` | 分组ID: ${groupId}`}
        </p>
      </Modal>

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
    </div>
  )
}