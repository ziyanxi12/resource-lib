import { useState, useEffect } from 'react'
import { Button, Modal, Input, Select, message, List, Tabs, Tag, Table, Space, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { api, Source, GroupNode, SearchApp } from '../api'

const RESOURCE_TYPE_OPTIONS = [
  { value: 'component', label: '组件' },
  { value: 'icon', label: '图标' },
  { value: 'illus', label: '插画' },
  { value: 'image', label: '图片' },
  { value: 'file', label: '文件' },
]

const RESOURCE_TYPE_ID_TO_NAME: Record<number, string> = {
  1: 'component',
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
  const [activeTab, setActiveTab] = useState('source')

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
        items={[
          {
            key: 'source',
            label: '来源与分组',
            children: <SourcePanel />,
          },
          {
            key: 'app',
            label: '应用管理',
            children: <SearchAppPanel />,
          },
        ]}
      />
    </div>
  )
}

function SourcePanel() {
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

  // 标签管理（只读）
  const [tags, setTags] = useState<string[]>([])
  const [tagLoading, setTagLoading] = useState(false)

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
                    {item.created_by && (
                      <div style={{ fontSize: 11, color: '#cbd5e1' }}>创建者: {item.created_by}</div>
                    )}
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
                            <Tag style={{ margin: 0 }}>{item}</Tag>
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

function SearchAppPanel() {
  const [apps, setApps] = useState<SearchApp[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newRemark, setNewRemark] = useState('')
  const [editOpen, setEditOpen] = useState(false)
  const [editingApp, setEditingApp] = useState<SearchApp | null>(null)
  const [editName, setEditName] = useState('')
  const [editRemark, setEditRemark] = useState('')
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deletingApp, setDeletingApp] = useState<SearchApp | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const loadApps = async () => {
    setLoading(true)
    try {
      const data = await api.getSearchApps()
      setApps(data.items)
    } catch {
      message.error('加载应用失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadApps()
  }, [])

  const handleCreate = async () => {
    if (!newName.trim()) {
      message.error('请输入应用名称')
      return
    }
    try {
      await api.createSearchApp({ name: newName.trim(), remark: newRemark.trim() || undefined })
      message.success('创建成功')
      setCreateOpen(false)
      setNewName('')
      setNewRemark('')
      loadApps()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '创建失败')
    }
  }

  const handleEdit = async () => {
    if (!editingApp || !editName.trim()) {
      message.error('请输入应用名称')
      return
    }
    try {
      await api.updateSearchApp(editingApp.id, { name: editName.trim(), remark: editRemark.trim() || undefined })
      message.success('修改成功')
      setEditOpen(false)
      setEditingApp(null)
      loadApps()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '修改失败')
    }
  }

  const handleDelete = async () => {
    if (!deletingApp) return
    setDeleteLoading(true)
    try {
      await api.deleteSearchApp(deletingApp.id)
      message.success('删除成功')
      setDeleteOpen(false)
      setDeletingApp(null)
      loadApps()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    } finally {
      setDeleteLoading(false)
    }
  }

  const copyAppId = (appId: string) => {
    navigator.clipboard.writeText(appId).then(() => {
      message.success('已复制 app_id')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  const columns: ColumnsType<SearchApp> = [
    {
      title: 'app_id',
      dataIndex: 'app_id',
      width: 320,
      render: (v: string) => (
        <Space>
          <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{v}</span>
          <Tooltip title="复制">
            <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyAppId(v)} />
          </Tooltip>
        </Space>
      ),
    },
    { title: '名称', dataIndex: 'name', width: 160 },
    { title: '备注', dataIndex: 'remark', width: 200, render: (v: string | null) => v ?? '—' },
    {
      title: '状态', dataIndex: 'is_active', width: 80,
      render: (v: number) => v === 1 ? <Tag color="green">启用</Tag> : <Tag color="default">禁用</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', width: 180, render: (v: number) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '—' },
    {
      title: '操作', width: 120, fixed: 'right',
      render: (_: unknown, record: SearchApp) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => {
            setEditingApp(record)
            setEditName(record.name)
            setEditRemark(record.remark ?? '')
            setEditOpen(true)
          }} />
          <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => {
            setDeletingApp(record)
            setDeleteOpen(true)
          }} />
        </Space>
      ),
    },
  ]

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>应用管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新增应用</Button>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <Table<SearchApp>
          rowKey="id"
          size="small"
          loading={loading}
          columns={columns}
          dataSource={apps}
          scroll={{ x: 'max-content', y: 'calc(100vh - 280px)' }}
          pagination={false}
        />
      </div>

      {/* 新增应用弹窗 */}
      <Modal
        title="新增应用"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); setNewName(''); setNewRemark('') }}
        onOk={handleCreate}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>名称 <span style={{ color: '#ef4444' }}>*</span></div>
          <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="请输入应用名称" />
        </div>
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>备注</div>
          <Input.TextArea value={newRemark} onChange={e => setNewRemark(e.target.value)} placeholder="请输入备注（选填）" autoSize={{ minRows: 2 }} />
        </div>
        <div style={{ marginTop: 12, color: '#94a3b8', fontSize: 12 }}>
          创建后系统自动生成 app_id（不可修改），可用于配置前端 VITE_FRONTEND_APP_ID。
        </div>
      </Modal>

      {/* 编辑应用弹窗 */}
      <Modal
        title="编辑应用"
        open={editOpen}
        onCancel={() => { setEditOpen(false); setEditingApp(null) }}
        onOk={handleEdit}
        okText="确定"
        cancelText="取消"
      >
        {editingApp && (
          <div style={{ marginBottom: 16, padding: '8px 12px', background: '#f8fafc', borderRadius: 6 }}>
            <span style={{ color: '#64748b', fontSize: 13 }}>app_id: </span>
            <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{editingApp.app_id}</span>
          </div>
        )}
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>名称 <span style={{ color: '#ef4444' }}>*</span></div>
          <Input value={editName} onChange={e => setEditName(e.target.value)} placeholder="请输入应用名称" />
        </div>
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>备注</div>
          <Input.TextArea value={editRemark} onChange={e => setEditRemark(e.target.value)} placeholder="请输入备注（选填）" autoSize={{ minRows: 2 }} />
        </div>
      </Modal>

      {/* 删除应用弹窗 */}
      <Modal
        title="确认删除"
        open={deleteOpen}
        onCancel={() => { setDeleteOpen(false); setDeletingApp(null) }}
        onOk={handleDelete}
        okText="删除"
        okButtonProps={{ danger: true, loading: deleteLoading }}
        cancelText="取消"
      >
        <p>确定删除应用「{deletingApp?.name}」吗？</p>
        <p style={{ color: '#94a3b8', fontSize: 12 }}>删除后该 app_id 的历史搜索日志保留，但无法再对应到应用名称。</p>
      </Modal>
    </div>
  )
}