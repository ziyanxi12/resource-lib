import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Select, message, Modal, Input } from 'antd'
import { UploadOutlined, SyncOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import ResourceTable, { type ResourceTableHandle } from '../components/ResourceTable'
import GroupTree from '../components/GroupTree'
import { api, Source } from '../api'

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
  const tableRef = useRef<ResourceTableHandle | null>(null)
  const [groupId, setGroupId] = useState<number | null>(null)
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

  useEffect(() => {
    api.getSources()
      .then(data => {
        const typeNum = RESOURCE_TYPE_MAP[type]
        const filtered = data.items.filter(s => s.resource_type === typeNum)
        setSources(filtered)
        if (filtered.length > 0) {
          setSourceId(filtered[0].id)
        } else {
          setSourceId(null)
        }
      })
      .catch(() => message.error('加载来源失败'))
  }, [type])

  useEffect(() => {
    if (!sourceId) {
      setGroupId(null)
      return
    }
    
    api.getGroups(type, sourceId)
      .then(data => {
        if (data.items.length > 0) {
          const rootGroup = data.items.find(item => item.parent_id === null)
          if (rootGroup) {
            setGroupId(rootGroup.id)
          } else {
            setGroupId(data.items[0].id)
          }
        } else {
          setGroupId(null)
        }
      })
      .catch(() => {
        setGroupId(null)
      })
  }, [type, sourceId])

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
      const typeNum = RESOURCE_TYPE_MAP[type]
      const source = await api.createSource({
        name: newSourceName.trim(),
        resource_type: typeNum,
        is_sync_source: 0,
        is_active: 1,
      })
      
      await api.createGroup({
        resource_type: typeNum,
        source_id: source.id,
        name: '默认分组',
        parent_id: null,
      })
      
      message.success('创建成功')
      setCreateSourceModalOpen(false)
      setNewSourceName('')
      
      const data = await api.getSources()
      const filtered = data.items.filter(s => s.resource_type === typeNum)
      setSources(filtered)
      setSourceId(source.id)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '创建失败')
    } finally {
      setCreatingSource(false)
    }
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
    </div>
  )
}