import { useState, useEffect, useCallback } from 'react'
import { Tree, Button, Input, Dropdown, message, Modal } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { TreeDataNode, TreeProps } from 'antd'
import { api, GroupNode } from '../api'

interface GroupTreeProps {
  type: string
  selectedId?: number | null
  onSelect?: (id: number | null) => void
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

export default function GroupTree({ type, selectedId, onSelect, sourceId }: GroupTreeProps) {
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [addingParentId, setAddingParentId] = useState<number | null>(null)
  const [newName, setNewName] = useState('')
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([])
  const [deletePreview, setDeletePreview] = useState<{
    groups: Array<{ id: number; name: string; level: number }>
    resourceCount: number
  } | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [clearGroupId, setClearGroupId] = useState<number | null>(null)
  const [clearModalCount, setClearModalCount] = useState<number | null>(null)
  const [clearModalLoading, setClearModalLoading] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [movePreview, setMovePreview] = useState<{
    id: number
    name: string
    targetParentId: number | null
    targetParentName: string
    sortOrder: number
    resourceCount: number
  } | null>(null)
  const [moveLoading, setMoveLoading] = useState(false)

  const loadGroups = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getGroups(type, sourceId, false)
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
        type: type,
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

  const handleDelete = async (id: number) => {
    const getAllDescendants = (nodes: GroupNode[], targetId: number): GroupNode[] => {
      for (const node of nodes) {
        if (node.id === targetId) {
          return flattenWithChildren(node)
        }
        if (node.children) {
          const found = getAllDescendants(node.children, targetId)
          if (found.length) return found
        }
      }
      return []
    }

    const flattenWithChildren = (node: GroupNode): GroupNode[] => {
      let result = [node]
      if (node.children) {
        for (const child of node.children) {
          result = result.concat(flattenWithChildren(child))
        }
      }
      return result
    }

    const descendants = getAllDescendants(groups, id)
    setDeletingId(id)
    setDeleteLoading(true)
    try {
      const { count } = await api.getGroupResourceCount(id)
      setDeletePreview({
        groups: descendants.map(g => ({ id: g.id, name: g.name, level: g.level })),
        resourceCount: count,
      })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '获取资源数量失败')
      setDeletingId(null)
    } finally {
      setDeleteLoading(false)
    }
  }

  const confirmDelete = async () => {
    setDeleteLoading(true)
    try {
      await api.deleteGroup(deletingId!)
      message.success('删除成功')
      setDeletingId(null)
      setDeletePreview(null)
      if (selectedId === deletingId) {
        onSelect?.(null)
      }
      loadGroups()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    } finally {
      setDeleteLoading(false)
    }
  }

  const handleClearClick = async (groupId: number) => {
    setClearModalLoading(true)
    setClearGroupId(groupId)
    try {
      const { count } = await api.getGroupResourceCount(groupId)
      setClearModalCount(count)
    } catch {
      setClearModalCount(null)
    } finally {
      setClearModalLoading(false)
    }
  }

  const handleClear = async () => {
    if (!clearGroupId || !sourceId) return
    setClearing(true)
    try {
      const r = await api.clearResources(type, sourceId, clearGroupId)
      message.success(`已删除 ${r.deleted} 条数据`)
      setClearGroupId(null)
      setClearModalCount(null)
      loadGroups()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '清空失败')
    } finally {
      setClearing(false)
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

    const dragGroup = findGroupById(groups, Number(dragKey))
    const targetParentName = newParentId 
      ? findGroupById(groups, newParentId)?.name || '未知分组'
      : '根级别'

    setMoveLoading(true)
    try {
      const { count } = await api.getGroupResourceCount(Number(dragKey))
      setMovePreview({
        id: Number(dragKey),
        name: dragGroup?.name || '',
        targetParentId: newParentId,
        targetParentName,
        sortOrder: newSortOrder,
        resourceCount: count,
      })
    } catch (e) {
      message.error('获取资源数量失败')
    } finally {
      setMoveLoading(false)
    }
  }

  const confirmMove = async () => {
    if (!movePreview) return
    setMoveLoading(true)
    try {
      await api.moveGroup(movePreview.id, {
        parent_id: movePreview.targetParentId,
        sort_order: movePreview.sortOrder,
      })
      message.success('移动成功')
      setMovePreview(null)
      loadGroups()
    } catch (e) {
      message.error('移动失败: ' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setMoveLoading(false)
    }
  }

  const treeData = convertToTreeData(groups)

  const findGroupById = (nodes: GroupNode[], targetId: number): GroupNode | null => {
    for (const node of nodes) {
      if (node.id === targetId) return node
      if (node.children) {
        const found = findGroupById(node.children, targetId)
        if (found) return found
      }
    }
    return null
  }

  const titleRender = (node: TreeDataNode) => {
    const id = Number(node.key)
    const name = String(node.title)
    const group = findGroupById(groups, id)
    const isRoot = group?.parent_id === null || group?.parent_id === undefined

    const menuItems: Array<{ key: string; label: string; icon: React.ReactNode; danger?: boolean }> = [
      { key: 'add', label: '新增子分组', icon: <PlusOutlined /> },
      { key: 'edit', label: '编辑名称', icon: <EditOutlined /> },
    ]
    
    if (!isRoot) {
      menuItems.push({ key: 'delete', label: '删除分组', icon: <DeleteOutlined />, danger: true })
    }
    
    menuItems.push({ key: 'clear', label: '清空数据', icon: <DeleteOutlined />, danger: true })

    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          gap: 8,
        }}
        onContextMenu={(e) => {
          e.preventDefault()
        }}
      >
        <span
          style={{
            flex: 1,
            minWidth: 0,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {name}
          {group?.resource_count !== undefined && (
            <span style={{ color: '#94a3b8', marginLeft: 6, fontSize: 12 }}>
              ({group.resource_count})
            </span>
          )}
        </span>
        <Dropdown
          menu={{
            items: menuItems,
            onClick: ({ key }) => {
              if (key === 'add') handleAddChild(id)
              if (key === 'edit') handleEdit(id, name)
              if (key === 'delete') handleDelete(id)
              if (key === 'clear') handleClearClick(id)
            },
          }}
          trigger={['click']}
        >
          <Button
            size="small"
            type="text"
            icon={<PlusOutlined />}
            style={{ flexShrink: 0, opacity: 0.5 }}
            onClick={(e) => e.stopPropagation()}
          />
        </Dropdown>
      </div>
    )
  }

  return (
    <div style={{ background: '#fff', borderRadius: 8, padding: 12, height: '100%', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 12 }}>
        <span style={{ fontWeight: 600, fontSize: 14 }}>分组</span>
      </div>

      <style>{`
        .group-tree .ant-tree-treenode {
          padding: 1px 0 !important;
          margin: 0 !important;
          width: 100% !important;
        }
        .group-tree .ant-tree-node-content-wrapper {
          height: 28px !important;
          line-height: 28px !important;
          padding: 0 6px !important;
          border-radius: 4px;
          transition: background 0.15s;
          max-width: calc(100% - 40px) !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
          white-space: nowrap !important;
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
        open={editingId !== null}
        title="编辑分组名称"
        onCancel={() => {
          setEditingId(null)
          setEditingName('')
        }}
        onOk={handleSaveEdit}
      >
        <Input
          placeholder="请输入分组名称"
          value={editingName}
          onChange={e => setEditingName(e.target.value)}
          autoFocus
        />
      </Modal>

      <Modal
        open={deletingId !== null}
        title="确认删除"
        onCancel={() => {
          setDeletingId(null)
          setDeletePreview(null)
        }}
        onOk={confirmDelete}
        okText="删除"
        okButtonProps={{ danger: true, loading: deleteLoading }}
      >
        {deleteLoading && !deletePreview ? (
          <p style={{ color: '#64748b' }}>加载中...</p>
        ) : deletePreview ? (
          <>
            <p style={{ marginBottom: 8 }}>以下分组将被删除：</p>
            <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
              {deletePreview.groups.map(g => (
                <li key={g.id}>
                  {g.name}
                  {g.level > 0 && <span style={{ color: '#94a3b8', marginLeft: 8 }}>(子分组)</span>}
                </li>
              ))}
            </ul>
            <p>
              共 <strong style={{ color: '#ef4444' }}>{deletePreview.resourceCount}</strong> 条资源数据将移入"默认分组"
            </p>
          </>
        ) : null}
      </Modal>

      <Modal
        open={clearGroupId !== null}
        title="确认清空"
        onCancel={() => {
          setClearGroupId(null)
          setClearModalCount(null)
        }}
        onOk={handleClear}
        okText="确认清空"
        okButtonProps={{ danger: true, loading: clearing }}
      >
        {clearModalLoading ? (
          <p style={{ color: '#64748b' }}>正在统计数据...</p>
        ) : (
          <p>确定清空当前分组的所有数据吗？</p>
        )}
        {clearModalCount !== null && !clearModalLoading && (
          <p style={{ fontWeight: 500 }}>
            即将删除 <span style={{ color: '#ef4444' }}>{clearModalCount}</span> 条数据
          </p>
        )}
      </Modal>

      <Modal
        open={movePreview !== null}
        title="确认移动"
        onCancel={() => setMovePreview(null)}
        onOk={confirmMove}
        okText="确认移动"
        okButtonProps={{ loading: moveLoading }}
      >
        {moveLoading && !movePreview ? (
          <p style={{ color: '#64748b' }}>加载中...</p>
        ) : movePreview ? (
          <>
            <p>
              确定将分组 <strong>{movePreview.name}</strong> 移动到 <strong>{movePreview.targetParentName}</strong> 吗？
            </p>
            <p>
              该分组及其子分组共 <strong style={{ color: '#ef4444' }}>{movePreview.resourceCount}</strong> 条资源将一起移动。
            </p>
          </>
        ) : null}
      </Modal>
    </div>
  )
}