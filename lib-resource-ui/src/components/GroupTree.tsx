import { useState, useEffect, useCallback } from 'react'
import { Tree, Button, Input, Dropdown, message, Modal } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { TreeDataNode, TreeProps } from 'antd'
import { api, GroupNode } from '../api'

interface GroupTreeProps {
  type: string
  selectedId?: number | null
  onSelect?: (id: number | null) => void
  width?: number
  sourceId?: number | null
}

const RESOURCE_TYPE_MAP: Record<string, number> = {
  component: 1,
  template: 2,
  icon: 3,
  illus: 4,
  image: 5,
  file: 6,
}

function convertToTreeData(groups: GroupNode[]): TreeDataNode[] {
  return groups.map(g => ({
    key: g.id,
    title: g.name,
    children: convertToTreeData(g.children),
  }))
}

export default function GroupTree({ type, selectedId, onSelect, width = 240, sourceId }: GroupTreeProps) {
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [addingParentId, setAddingParentId] = useState<number | null>(null)
  const [newName, setNewName] = useState('')
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([])

  const loadGroups = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getGroups(type, sourceId)
      setGroups(data.items)
    } catch (e) {
      message.error('加载分组失败')
    } finally {
      setLoading(false)
    }
  }, [type, sourceId])

  useEffect(() => {
    loadGroups()
  }, [loadGroups])

  useEffect(() => {
    const getAllKeys = (nodes: GroupNode[]): React.Key[] => {
      const keys: React.Key[] = []
      nodes.forEach(node => {
        keys.push(node.id)
        if (node.children?.length) {
          keys.push(...getAllKeys(node.children))
        }
      })
      return keys
    }
    setExpandedKeys(getAllKeys(groups))
  }, [groups])

  const handleSelect: TreeProps['onSelect'] = (selectedKeys) => {
    const key = selectedKeys[0]
    onSelect?.(key ? Number(key) : null)
  }

  const handleAddRoot = () => {
    setAddingParentId(null)
    setNewName('')
    setIsAdding(true)
  }

  const handleAddChild = (parentId: number) => {
    setAddingParentId(parentId)
    setNewName('')
    setIsAdding(true)
  }

  const handleCreate = async () => {
    if (!newName.trim()) {
      message.warning('请输入分组名称')
      return
    }
    try {
      await api.createGroup({
        resource_type: RESOURCE_TYPE_MAP[type],
        name: newName.trim(),
        parent_id: addingParentId,
        source_id: sourceId ?? undefined,
      })
      message.success('创建成功')
      setIsAdding(false)
      setAddingParentId(null)
      setNewName('')
      loadGroups()
    } catch (e) {
      message.error('创建失败')
    }
  }

  const handleEdit = (id: number, name: string) => {
    setEditingId(id)
    setEditingName(name)
  }

  const handleSaveEdit = async () => {
    if (!editingName.trim()) {
      message.warning('请输入分组名称')
      return
    }
    try {
      await api.updateGroup(editingId!, { name: editingName.trim() })
      message.success('更新成功')
      setEditingId(null)
      setEditingName('')
      loadGroups()
    } catch (e) {
      message.error('更新失败')
    }
  }

  const handleDelete = (id: number) => {
    setDeletingId(id)
  }

  const confirmDelete = async () => {
    try {
      await api.deleteGroup(deletingId!)
      message.success('删除成功')
      setDeletingId(null)
      if (selectedId === deletingId) {
        onSelect?.(null)
      }
      loadGroups()
    } catch (e) {
      message.error('删除失败')
    }
  }

  const handleDrop: TreeProps['onDrop'] = async (info) => {
    const dropKey = info.node.key
    const dragKey = info.dragNode.key
    const dropPos = info.dropPosition

    let newParentId: number | null = null
    let newSortOrder = 0

    const findParentKey = (nodes: TreeDataNode[], targetKey: React.Key, parentKey: React.Key | null = null): React.Key | null => {
      for (const node of nodes) {
        if (node.key === targetKey) return parentKey
        if (node.children) {
          const found = findParentKey(node.children, targetKey, node.key)
          if (found !== undefined) return found
        }
      }
      return null
    }

    if (info.dropToGap) {
      const parentKey = findParentKey(treeData, dropKey)
      newParentId = parentKey ? Number(parentKey) : null
      newSortOrder = dropPos
    } else {
      newParentId = Number(dropKey)
      newSortOrder = 0
    }

    try {
      await api.moveGroup(Number(dragKey), {
        parent_id: newParentId,
        sort_order: newSortOrder,
      })
      message.success('移动成功')
      loadGroups()
    } catch (e) {
      message.error('移动失败: ' + (e instanceof Error ? e.message : '未知错误'))
    }
  }

  const treeData = convertToTreeData(groups)

  const titleRender = (node: TreeDataNode) => {
    const id = Number(node.key)
    const name = String(node.title)
    const group = groups.find(g => g.id === id)
    const isRoot = group?.parent_id === null || group?.parent_id === undefined

    if (editingId === id) {
      return (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Input
            size="small"
            value={editingName}
            onChange={e => setEditingName(e.target.value)}
            style={{ width: 120 }}
            autoFocus
          />
          <Button size="small" type="primary" onClick={handleSaveEdit}>保存</Button>
          <Button size="small" onClick={() => setEditingId(null)}>取消</Button>
        </div>
      )
    }

    const menuItems: Array<{ key: string; label: string; icon: React.ReactNode; danger?: boolean }> = [
      { key: 'add', label: '新增子分组', icon: <PlusOutlined /> },
      { key: 'edit', label: '编辑名称', icon: <EditOutlined /> },
    ]
    
    if (!isRoot) {
      menuItems.push({ key: 'delete', label: '删除分组', icon: <DeleteOutlined />, danger: true })
    }

    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          paddingRight: 8,
        }}
        onContextMenu={(e) => {
          e.preventDefault()
        }}
      >
        <span
          style={{
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {name}
        </span>
        <Dropdown
          menu={{
            items: menuItems,
            onClick: ({ key }) => {
              if (key === 'add') handleAddChild(id)
              if (key === 'edit') handleEdit(id, name)
              if (key === 'delete') handleDelete(id)
            },
          }}
          trigger={['click']}
        >
          <Button
            size="small"
            type="text"
            icon={<PlusOutlined />}
            style={{ opacity: 0.5 }}
          />
        </Dropdown>
      </div>
    )
  }

  return (
    <div style={{ width, background: '#fff', borderRadius: 8, padding: 12, height: '100%', overflow: 'auto' }}>
      <div style={{ marginBottom: 12 }}>
        <span style={{ fontWeight: 600, fontSize: 14 }}>分组</span>
      </div>

      <style>{`
        .group-tree .ant-tree-treenode {
          padding: 1px 0 !important;
          margin: 0 !important;
        }
        .group-tree .ant-tree-node-content-wrapper {
          height: 28px !important;
          line-height: 28px !important;
          padding: 0 6px !important;
          border-radius: 4px;
          transition: background 0.15s;
        }
        .group-tree .ant-tree-node-content-wrapper:hover {
          background: #f1f5f9;
        }
        .group-tree .ant-tree-node-content-wrapper.ant-tree-node-selected {
          background: #e0e7ff !important;
        }
        .group-tree .ant-tree-switcher {
          width: 18px !important;
          line-height: 28px !important;
        }
      `}</style>
      <div className="group-tree">
        <Tree
          treeData={treeData}
          selectedKeys={selectedId ? [selectedId] : []}
          expandedKeys={expandedKeys}
          onExpand={setExpandedKeys}
          onSelect={handleSelect}
          titleRender={titleRender}
          draggable
          onDrop={handleDrop}
          blockNode
          style={{ fontSize: 13 }}
        />
      </div>

      <Modal
        open={isAdding}
        title="新增分组"
        onCancel={() => {
          setIsAdding(false)
          setAddingParentId(null)
          setNewName('')
        }}
        onOk={handleCreate}
      >
        <Input
          placeholder="请输入分组名称"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          autoFocus
        />
      </Modal>

      <Modal
        open={deletingId !== null}
        title="确认删除"
        onCancel={() => setDeletingId(null)}
        onOk={confirmDelete}
        okText="删除"
        okButtonProps={{ danger: true }}
      >
        <p>删除分组后，该分组下的资源将归入"未分类"，确定删除吗？</p>
      </Modal>
    </div>
  )
}