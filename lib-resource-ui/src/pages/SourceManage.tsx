import { useState, useEffect } from 'react'
import { Button, Modal, Input, Select, message, List } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { api, Source, GroupNode } from '../api'

const RESOURCE_TYPE_OPTIONS = [
  { value: 'component', label: '组件' },
  { value: 'template', label: '模版' },
  { value: 'icon', label: '图标' },
  { value: 'illus', label: '插画' },
  { value: 'image', label: '图片' },
  { value: 'file', label: '文件' },
]

const RESOURCE_TYPE_ID_TO_NAME: Record<number, string> = {
  1: 'component',
  2: 'template',
  3: 'icon',
  4: 'illus',
  5: 'image',
  6: 'file',
}

const getTypeLabel = (resourceType: number) => {
  const option = RESOURCE_TYPE_OPTIONS.find(o => o.value === RESOURCE_TYPE_ID_TO_NAME[resourceType])
  return option?.label || '未知'
}

export default function SourceManage() {
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [loading, setLoading] = useState(false)

  // 新增来源
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState<string>('icon')

  // 编辑来源
  const [editSourceModalOpen, setEditSourceModalOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<Source | null>(null)
  const [editSourceName, setEditSourceName] = useState('')

  // 删除来源
  const [deleteSourceModalOpen, setDeleteSourceModalOpen] = useState(false)
  const [deletingSource, setDeletingSource] = useState<Source | null>(null)
  const [deleteSourceLoading, setDeleteSourceLoading] = useState(false)

  // 编辑分组
  const [editGroupModalOpen, setEditGroupModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<GroupNode | null>(null)
  const [editGroupName, setEditGroupName] = useState('')

  useEffect(() => {
    loadSources()
  }, [])

  useEffect(() => {
    if (selectedSource) {
      loadGroups(selectedSource.resource_type, selectedSource.id)
    } else {
      setGroups([])
    }
  }, [selectedSource])

  const loadSources = async () => {
    setLoading(true)
    try {
      const data = await api.getSources()
      setSources(data.items)
      if (data.items.length > 0 && !selectedSource) {
        setSelectedSource(data.items[0])
      }
    } catch {
      message.error('加载来源失败')
    } finally {
      setLoading(false)
    }
  }

  const loadGroups = async (resourceType: number, sourceId: number) => {
    try {
      const typeStr = RESOURCE_TYPE_ID_TO_NAME[resourceType]
      if (!typeStr) {
        throw new Error('未知资源类型')
      }
      const data = await api.getGroups(typeStr, sourceId)
      setGroups(flattenGroups(data.items))
    } catch {
      message.error('加载分组失败')
    }
  }

  const flattenGroups = (nodes: GroupNode[]): GroupNode[] => {
    const result: GroupNode[] = []
    const walk = (node: GroupNode) => {
      result.push(node)
      if (node.children) {
        node.children.forEach(walk)
      }
    }
    nodes.forEach(walk)
    return result
  }

  const handleCreate = async () => {
    if (!newName.trim()) {
      message.error('请输入名称')
      return
    }
    try {
      await api.createSource({
        name: newName.trim(),
        type: newType,
        is_sync_source: 0,
        is_active: 1,
      })
      message.success('创建成功')
      setCreateModalOpen(false)
      setNewName('')
      setNewType('icon')
      loadSources()
    } catch {
      message.error('创建失败')
    }
  }

  const handleEditSource = async () => {
    if (!editingSource || !editSourceName.trim()) {
      message.error('请输入名称')
      return
    }
    try {
      await api.updateSource(editingSource.id, { name: editSourceName.trim() })
      message.success('修改成功')
      setEditSourceModalOpen(false)
      setEditingSource(null)
      setEditSourceName('')
      loadSources()
    } catch {
      message.error('修改失败')
    }
  }

  const handleDeleteSource = async () => {
    if (!deletingSource) return
    
    setDeleteSourceLoading(true)
    try {
      await api.deleteSource(deletingSource.id)
      message.success('删除成功')
      setDeleteSourceModalOpen(false)
      setDeletingSource(null)
      if (selectedSource?.id === deletingSource.id) {
        setSelectedSource(null)
      }
      loadSources()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    } finally {
      setDeleteSourceLoading(false)
    }
  }

  const handleEditGroup = async () => {
    if (!editingGroup || !editGroupName.trim()) {
      message.error('请输入名称')
      return
    }
    try {
      await api.updateGroup(editingGroup.id, { name: editGroupName.trim() })
      message.success('修改成功')
      setEditGroupModalOpen(false)
      setEditingGroup(null)
      setEditGroupName('')
      if (selectedSource) {
        loadGroups(selectedSource.resource_type, selectedSource.id)
      }
    } catch {
      message.error('修改失败')
    }
  }

  const handleGetGroups = async () => {
    if (!selectedSource) return
    try {
      const typeStr = RESOURCE_TYPE_ID_TO_NAME[selectedSource.resource_type]
      if (!typeStr) {
        throw new Error('未知资源类型')
      }
      const data = await api.getGroups(typeStr, selectedSource.id)
      const jsonStr = JSON.stringify(data, null, 2)
      await navigator.clipboard.writeText(jsonStr)
      message.success('已复制到剪贴板')
    } catch {
      message.error('获取分组失败')
    }
  }

  const openEditSourceModal = (source: Source) => {
    setEditingSource(source)
    setEditSourceName(source.name)
    setEditSourceModalOpen(true)
  }

  const openEditGroupModal = (group: GroupNode) => {
    setEditingGroup(group)
    setEditGroupName(group.name)
    setEditGroupModalOpen(true)
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600 }}>来源与分组管理</h2>
      
      <div style={{ flex: 1, display: 'flex', gap: 16, minHeight: 0 }}>
        {/* 左侧：来源列表 */}
        <div style={{ 
          width: 300, 
          flexShrink: 0,
          border: '1px solid #e2e8f0', 
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{ 
            padding: '12px 16px', 
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ fontWeight: 500 }}>来源</span>
            <Button 
              type="primary" 
              size="small" 
              icon={<PlusOutlined />}
              onClick={() => setCreateModalOpen(true)}
            >
              新增
            </Button>
          </div>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <List
              dataSource={sources}
              loading={loading}
              renderItem={(item) => (
                <List.Item
                  style={{
                    padding: '12px 16px',
                    background: selectedSource?.id === item.id ? '#f0f9ff' : 'transparent',
                    borderLeft: selectedSource?.id === item.id ? '3px solid #3b82f6' : '3px solid transparent',
                  }}
                >
                  <div 
                    style={{ flex: 1, cursor: 'pointer' }}
                    onClick={() => setSelectedSource(item)}
                  >
                    <div style={{ fontSize: 13, color: '#64748b' }}>ID: {item.id}</div>
                    <div style={{ fontWeight: 500 }}>{item.name}</div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>{getTypeLabel(item.resource_type)}</div>
                  </div>
                  <Button 
                    type="text" 
                    size="small" 
                    icon={<EditOutlined />}
                    onClick={(e) => {
                      e.stopPropagation()
                      openEditSourceModal(item)
                    }}
                  />
                  <Button 
                    type="text" 
                    size="small" 
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => {
                      e.stopPropagation()
                      setDeletingSource(item)
                      setDeleteSourceModalOpen(true)
                    }}
                  />
                </List.Item>
              )}
            />
          </div>
        </div>

        {/* 右侧：分组列表 */}
        <div style={{ 
          flex: 1,
          border: '1px solid #e2e8f0', 
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{ 
            padding: '12px 16px', 
            borderBottom: '1px solid #e2e8f0',
            fontWeight: 500,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span>分组 {selectedSource && `（来源：${selectedSource.name}）`}</span>
            {selectedSource && (
              <Button size="small" onClick={handleGetGroups}>
                获取分组
              </Button>
            )}
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
            {selectedSource ? (
              groups.length > 0 ? (
                <List
                  dataSource={groups}
                  renderItem={(item) => (
                    <List.Item style={{ padding: '8px 12px' }}>
                      <div style={{ fontSize: 13, color: '#64748b', width: 60 }}>ID: {item.id}</div>
                      <div style={{ flex: 1 }}>{item.name}</div>
                      <Button 
                        type="text" 
                        size="small" 
                        icon={<EditOutlined />}
                        onClick={() => openEditGroupModal(item)}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ color: '#94a3b8', textAlign: 'center', padding: 40 }}>
                  暂无分组
                </div>
              )
            ) : (
              <div style={{ color: '#94a3b8', textAlign: 'center', padding: 40 }}>
                请选择来源
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 新增来源弹窗 */}
      <Modal
        title="新增来源"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={handleCreate}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>名称</div>
          <Input 
            value={newName} 
            onChange={e => setNewName(e.target.value)} 
            placeholder="请输入来源名称"
          />
        </div>
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>资源类型</div>
          <Select
            value={newType}
            onChange={setNewType}
            options={RESOURCE_TYPE_OPTIONS}
            style={{ width: '100%' }}
          />
        </div>
      </Modal>

      {/* 编辑来源弹窗 */}
      <Modal
        title="编辑来源"
        open={editSourceModalOpen}
        onCancel={() => {
          setEditSourceModalOpen(false)
          setEditingSource(null)
          setEditSourceName('')
        }}
        onOk={handleEditSource}
        okText="确定"
        cancelText="取消"
      >
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>名称</div>
          <Input 
            value={editSourceName} 
            onChange={e => setEditSourceName(e.target.value)} 
            placeholder="请输入来源名称"
          />
        </div>
      </Modal>

      {/* 编辑分组弹窗 */}
      <Modal
        title="编辑分组"
        open={editGroupModalOpen}
        onCancel={() => {
          setEditGroupModalOpen(false)
          setEditingGroup(null)
          setEditGroupName('')
        }}
        onOk={handleEditGroup}
        okText="确定"
        cancelText="取消"
      >
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>名称</div>
          <Input 
            value={editGroupName} 
            onChange={e => setEditGroupName(e.target.value)} 
            placeholder="请输入分组名称"
          />
        </div>
      </Modal>

      {/* 删除来源弹窗 */}
      <Modal
        title="确认删除"
        open={deleteSourceModalOpen}
        onCancel={() => {
          setDeleteSourceModalOpen(false)
          setDeletingSource(null)
        }}
        onOk={handleDeleteSource}
        okText="删除"
        okButtonProps={{ danger: true, loading: deleteSourceLoading }}
      >
        <p>确定删除来源「{deletingSource?.name}」吗？</p>
        <p style={{ color: '#94a3b8', fontSize: 12 }}>如果该来源下有资源，删除将失败。</p>
      </Modal>
    </div>
  )
}