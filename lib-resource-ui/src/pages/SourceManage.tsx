import { useState, useEffect, useRef } from 'react'
import { Button, Modal, Input, Select, message, Tabs, Tag, Table, Space, Tooltip, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { api, SearchApp, WhitelistAccount } from '../api'

export default function SourceManage() {
  const [activeTab, setActiveTab] = useState('app')

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
        items={[
          {
            key: 'app',
            label: '应用管理',
            children: <SearchAppPanel />,
          },
          {
            key: 'whitelist',
            label: '人员管理',
            children: <WhitelistPanel />,
          },
        ]}
      />
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

function WhitelistPanel() {
  const [list, setList] = useState<WhitelistAccount[]>([])
  const [loading, setLoading] = useState(false)

  const [userOptions, setUserOptions] = useState<{ value: string; label: string; dept?: string[] }[]>([])
  const [pendingUsers, setPendingUsers] = useState<Array<{ value: string; label: string }>>([])
  const [searching, setSearching] = useState(false)
  const [adding, setAdding] = useState(false)
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const userMapRef = useRef<Map<string, { nickName: string; dept?: string[] }>>(new Map())

  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState<WhitelistAccount | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const loadList = async () => {
    setLoading(true)
    try {
      const data = await api.getWhitelist()
      setList(data.items)

      data.items.filter(r => !r.nick_name).forEach(async (r) => {
        try {
          const result = await api.searchUsers(r.account)
          const match = result.items.find(
            u => u.account.toLowerCase() === r.account.toLowerCase()
          )
          if (match?.nickName) {
            await api.updateWhitelistAccount(r.id, { nick_name: match.nickName })
            setList(prev => prev.map(item =>
              item.id === r.id ? { ...item, nick_name: match.nickName } : item
            ))
          }
        } catch (e) {
          console.error('补全 nick_name 失败:', r.account, e)
        }
      })
    } catch {
      message.error('加载白名单失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadList()
  }, [])

  const handleSearchUser = (value: string) => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    if (abortRef.current) abortRef.current.abort()
    if (!value.trim()) {
      setUserOptions([])
      setSearching(false)
      return
    }
    debounceTimer.current = setTimeout(async () => {
      const controller = new AbortController()
      abortRef.current = controller
      const timeoutId = setTimeout(() => controller.abort(), 6000)
      setSearching(true)
      try {
        const data = await api.searchUsers(value.trim(), controller.signal)
        userMapRef.current.clear()
        data.items.forEach(u => userMapRef.current.set(u.account, { nickName: u.nickName, dept: u.dept }))
        setUserOptions(data.items.map(u => ({
          value: u.account,
          label: u.nickName,
          dept: u.dept,
        })))
      } catch (e: unknown) {
        if (e instanceof DOMException && e.name === 'AbortError') {
          message.warning('搜索超时，请重试')
        }
        setUserOptions([])
      } finally {
        clearTimeout(timeoutId)
        setSearching(false)
      }
    }, 300)
  }

  const handleBatchAdd = async () => {
    if (pendingUsers.length === 0) {
      message.warning('请先选择要添加的用户')
      return
    }
    setAdding(true)
    try {
      const accounts = pendingUsers.map(u => ({
        account: u.value,
        nick_name: u.label || undefined,
      }))
      const r = await api.batchCreateWhitelist(accounts)
      message.success(`添加完成：新增 ${r.created} 个，跳过 ${r.skipped} 个`)
      setPendingUsers([])
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '添加失败')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async () => {
    if (!deleting) return
    setDeleteLoading(true)
    try {
      await api.deleteWhitelistAccount(deleting.id)
      message.success('删除成功')
      setDeleteOpen(false)
      setDeleting(null)
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    } finally {
      setDeleteLoading(false)
    }
  }

  const columns: ColumnsType<WhitelistAccount> = [
    { title: '账号', dataIndex: 'account', width: 200, render: (v: string) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{v}</span> },
    { title: '昵称', dataIndex: 'nick_name', width: 160, render: (v: string | null) => v ?? '—' },
    { title: '备注', dataIndex: 'remark', width: 220, hidden: true, render: (v: string | null) => v ?? '—' },
    {
      title: '角色', dataIndex: 'role', width: 100,
      render: (_, record) => (
        <Select
          size="small"
          variant="borderless"
          value={record.role}
          style={{ width: '100%' }}
          options={[
            { value: 'super', label: <Tag color="purple" style={{ margin: 0 }}>超管</Tag> },
            { value: 'admin', label: <Tag style={{ margin: 0 }}>管理员</Tag> },
          ]}
          onChange={async (v) => {
            try {
              await api.updateWhitelistAccount(record.id, { role: v })
              message.success('角色已更新')
              setList(prev => prev.map(item =>
                item.id === record.id ? { ...item, role: v } : item
              ))
            } catch {
              message.error('更新失败')
            }
          }}
        />
      ),
    },
    {
      title: '状态', dataIndex: 'is_active', width: 90, hidden: true,
      render: (v: number) => v === 1 ? <Tag color="green">启用</Tag> : <Tag color="default">禁用</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', width: 180, render: (v: number) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '—' },
    {
      title: '操作', width: 60, fixed: 'right',
      render: (_: unknown, record: WhitelistAccount) => (
        <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => {
          setDeleting(record)
          setDeleteOpen(true)
        }} />
      ),
    },
  ]

  return (
    <div style={{ height: '100%', overflowY: 'auto', paddingRight: 4 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>人员管理</h2>
        <Space>
          <Select
            mode="multiple"
            labelInValue
            placeholder="搜索用户账号/昵称添加"
            style={{ width: 460 }}
            value={pendingUsers}
            options={userOptions}
            filterOption={false}
            onSearch={handleSearchUser}
            onChange={(val) => setPendingUsers(val as Array<{ value: string; label: string }>)}
            notFoundContent={searching ? <Spin size="small" /> : null}
            optionRender={(option) => {
              const info = userMapRef.current.get(option.value as string)
              const dept = info?.dept
              const deptText = dept?.length && dept.length >= 4
                ? `${dept[3]}[${dept[1]}]`
                : (dept?.length ? dept[0] : '')
              return (
                <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <span style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: '1 1 0',
                    textAlign: 'left',
                  }}>
                    {info?.nickName || option.label}
                  </span>
                  <span style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: '1 1 0',
                    textAlign: 'center',
                    color: '#94a3b8',
                    fontSize: 12,
                  }}>
                    {option.value}
                  </span>
                  {deptText && (
                    <span style={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: '1 1 0',
                      textAlign: 'right',
                      color: '#94a3b8',
                      fontSize: 12,
                    }}>
                      {deptText}
                    </span>
                  )}
                </div>
              )
            }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            loading={adding}
            disabled={pendingUsers.length === 0}
            onClick={handleBatchAdd}
          >
            添加{pendingUsers.length > 0 ? `(${pendingUsers.length})` : ''}
          </Button>
        </Space>
      </div>

      <div style={{ marginBottom: 12 }}>
        <Table<WhitelistAccount>
          rowKey="id"
          size="small"
          loading={loading}
          columns={columns}
          dataSource={list}
          scroll={{ x: 'max-content' }}
          pagination={false}
        />
      </div>

      {/* 删除账号弹窗 */}
      <Modal
        title="确认删除"
        open={deleteOpen}
        onCancel={() => { setDeleteOpen(false); setDeleting(null) }}
        onOk={handleDelete}
        okText="删除"
        okButtonProps={{ danger: true, loading: deleteLoading }}
        cancelText="取消"
      >
        <p>确定删除人员「{deleting?.account}」吗？</p>
        <p style={{ color: '#94a3b8', fontSize: 12 }}>删除后该账号将无法访问系统（在 WHITELIST_ENABLED=true 时生效），不可恢复。</p>
      </Modal>
    </div>
  )
}