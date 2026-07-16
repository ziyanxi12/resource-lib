import { useState, useEffect } from 'react'
import { Button, Modal, Input, Select, message, List } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { api, Source, GroupNode } from '../api'

const RESOURCE_TYPE_OPTIONS = [
  { value: 1, label: '组件' },
  { value: 2, label: '模版' },
  { value: 3, label: '图标' },
  { value: 4, label: '插画' },
  { value: 5, label: '图片' },
  { value: 6, label: '文件' },
]

export default function SourceManage() {
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [loading, setLoading] = useState(false)

  // 新增来源
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState<number>(3)

  // 编辑来源
  const [editSourceModalOpen, setEditSourceModalOpen] = useState(false)
  const [editingSource, setEditingSource] = useState<Source | null>(null)
  const [editSourceName, setEditSourceName] = useState('')

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
      const typeStr = ['component', 'template', 'icon', 'illus', 'image', 'file'][resourceType - 1]
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
        resource_type: newType,
        is_sync_source: 0,
        is_active: 1,
      })
      message.success('创建成功')
      setCreateModalOpen(false)
      setNewName('')
      setNewType(3)
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
      const typeStr = ['component', 'template', 'icon', 'illus', 'image', 'file'][selectedSource.resource_type - 1]
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

  const getTypeLabel = (type: number) => {
    const found = RESOURCE_TYPE_OPTIONS.find(o => o.value === type)
    return found?.label || '未知'
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
    </div>
  )
}