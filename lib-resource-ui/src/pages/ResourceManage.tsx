import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Select, TreeSelect, message, Modal, Input, Spin, Dropdown } from 'antd'
import { UploadOutlined, SyncOutlined, DeleteOutlined, PlusOutlined, EditOutlined, UndoOutlined, SettingOutlined, SwapOutlined } from '@ant-design/icons'
import ResourceTable, { type ResourceTableHandle } from '../components/ResourceTable'
import GroupTree, { type GroupTreeHandle } from '../components/GroupTree'
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
                    { type: 'divider' as const },
                    { key: 'sync', label: '向量同步', icon: <SyncOutlined spin={syncing} /> },
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
                    if (key === 'sync') handleSyncVectors()
                  },
                }}
                trigger={['click']}
                disabled={!sourceId}
              >
                <Button size="small" icon={<SettingOutlined />} disabled={!sourceId} />
              </Dropdown>
              <span
                style={{ fontSize: 12, color: '#64748b', cursor: 'pointer', marginLeft: 4, whiteSpace: 'nowrap' }}
                onClick={() => { loadTrashSources(); setTrashModalOpen(true) }}
              >
                回收站
              </span>
            </div>
          </div>

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
    </div>
  )
}