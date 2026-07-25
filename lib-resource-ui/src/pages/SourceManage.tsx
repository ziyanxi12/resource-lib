import { useState, useEffect } from 'react'
import { Button, Modal, Input, Select, message, List, Tabs, Tag } from 'antd'
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

  // 标签管理
  const [tags, setTags] = useState<{ tag: string; count: number }[]>([])
  const [tagLoading, setTagLoading] = useState(false)
  const [editTagModalOpen, setEditTagModalOpen] = useState(false)
  const [editingTag, setEditingTag] = useState<string | null>(null)
  const [editTagName, setEditTagName] = useState('')
  const [renameTagLoading, setRenameTagLoading] = useState(false)
  const [deleteTagLoading, setDeleteTagLoading] = useState(false)

  useEffect(() => {
    loadSources()
  }, [])

  useEffect(() => {
    if (selectedSource) {
      loadGroups(selectedSource.resource_type, selectedSource.id)
      loadTags(selectedSource.resource_type, selectedSource.id)
    } else {
      setGroups([])
      setTags([])
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

  const loadTags = async (resourceType: number, sourceId: number) => {
    const typeStr = RESOURCE_TYPE_ID_TO_NAME[resourceType]
    if (!typeStr) return
    setTagLoading(true)
    try {
      const data = await api.getTags(typeStr, sourceId)
      setTags(data.items)
    } catch {
      message.error('加载标签失败')
    } finally {
      setTagLoading(false)
    }
  }

  const openEditTagModal = (tag: string) => {
    setEditingTag(tag)
    setEditTagName(tag)
    setEditTagModalOpen(true)
  }

  const handleRenameTag = async () => {
    if (!selectedSource || !editingTag) return
    if (!editTagName.trim()) {
      message.error('请输入标签名')
      return
    }
    if (editTagName.trim() === editingTag) {
      message.warning('新标签名与原标签名相同')
      return
    }
    setRenameTagLoading(true)
    try {
      const typeStr = RESOURCE_TYPE_ID_TO_NAME[selectedSource.resource_type]
      const res = await api.renameTag({
        type: typeStr,
        sourceId: selectedSource.id,
        oldTag: editingTag,
        newTag: editTagName.trim(),
      })
      message.success(`已重命名，影响 ${res.affected} 条资源`)
      setEditTagModalOpen(false)
      setEditingTag(null)
      setEditTagName('')
      loadTags(selectedSource.resource_type, selectedSource.id)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '重命名失败')
    } finally {
      setRenameTagLoading(false)
    }
  }

  const handleDeleteTag = (tag: string) => {
    if (!selectedSource) return
    Modal.confirm({
      title: '确认删除标签',
      content: `确定删除标签「${tag}」吗？该操作会从当前来源下所有资源中移除此标签。`,
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        setDeleteTagLoading(true)
        try {
          const typeStr = RESOURCE_TYPE_ID_TO_NAME[selectedSource.resource_type]
          const res = await api.deleteTag({
            type: typeStr,
            sourceId: selectedSource.id,
            tag,
          })
          message.success(`已删除，影响 ${res.affected} 条资源`)
          loadTags(selectedSource.resource_type, selectedSource.id)
        } catch (e) {
          message.error(e instanceof Error ? e.message : '删除失败')
        } finally {
          setDeleteTagLoading(false)
        }
      },
    })
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

        {/* 右侧：分组/标签管理（Tab 切换） */}
        <div style={{ 
          flex: 1,
          border: '1px solid #e2e8f0', 
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
        }}>
          {selectedSource ? (
            <Tabs
              defaultActiveKey="group"
              style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
              tabBarStyle={{ padding: '0 16px', margin: 0 }}
              items={[
                {
                  key: 'group',
                  label: `分组（${groups.length}）`,
                  children: (
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
                      <div style={{ padding: '8px 16px', display: 'flex', justifyContent: 'flex-end' }}>
                        <Button size="small" onClick={handleGetGroups}>获取分组</Button>
                      </div>
                      <div style={{ flex: 1, overflow: 'auto', padding: '0 16px 16px' }}>
                        {groups.length > 0 ? (
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
                        )}
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'tag',
                  label: `标签（${tags.length}）`,
                  children: (
                    <div style={{ padding: '0 16px 16px' }}>
                      <List
                        loading={tagLoading}
                        dataSource={tags}
                        renderItem={(item) => (
                          <List.Item style={{ padding: '8px 12px' }}>
                            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                              <Tag style={{ margin: 0 }}>{item.tag}</Tag>
                              <span style={{ color: '#94a3b8', fontSize: 12 }}>{item.count} 条资源</span>
                            </div>
                            <Button 
                              type="text" 
                              size="small" 
                              icon={<EditOutlined />}
                              loading={renameTagLoading && editingTag === item.tag}
                              onClick={() => openEditTagModal(item.tag)}
                            />
                            <Button 
                              type="text" 
                              size="small" 
                              danger
                              icon={<DeleteOutlined />}
                              loading={deleteTagLoading && editingTag === item.tag}
                              onClick={() => handleDeleteTag(item.tag)}
                            />
                          </List.Item>
                        )}
                        locale={{ emptyText: '暂无标签' }}
                      />
                    </div>
                  ),
                },
              ]}
            />
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
              请选择来源
            </div>
          )}
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

      {/* 重命名标签弹窗 */}
      <Modal
        title="重命名标签"
        open={editTagModalOpen}
        onCancel={() => {
          setEditTagModalOpen(false)
          setEditingTag(null)
          setEditTagName('')
        }}
        onOk={handleRenameTag}
        okText="确定"
        okButtonProps={{ loading: renameTagLoading }}
        cancelText="取消"
      >
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>
            原标签：<Tag>{editingTag}</Tag>
          </div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>新标签名</div>
          <Input 
            value={editTagName} 
            onChange={e => setEditTagName(e.target.value)} 
            placeholder="请输入新标签名"
            onPressEnter={handleRenameTag}
          />
          <div style={{ marginTop: 8, color: '#94a3b8', fontSize: 12 }}>
            若新标签名已存在，将自动合并（去重）。
          </div>
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