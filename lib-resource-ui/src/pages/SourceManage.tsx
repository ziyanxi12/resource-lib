import { useState, useEffect } from 'react'
import { Button, Modal, Input, Select, message, Tabs, Tag, Table, Space, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ReloadOutlined, CheckCircleOutlined, StopOutlined } from '@ant-design/icons'
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
  const [isActive, setIsActive] = useState<number | undefined>(undefined)
  const [search, setSearch] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [newAccount, setNewAccount] = useState('')
  const [newRemark, setNewRemark] = useState('')

  const [batchOpen, setBatchOpen] = useState(false)
  const [batchText, setBatchText] = useState('')
  const [batchLoading, setBatchLoading] = useState(false)

  const [editOpen, setEditOpen] = useState(false)
  const [editing, setEditing] = useState<WhitelistAccount | null>(null)
  const [editNick, setEditNick] = useState('')
  const [editRemark, setEditRemark] = useState('')
  const [editRole, setEditRole] = useState<string>('admin')

  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState<WhitelistAccount | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const [refreshingId, setRefreshingId] = useState<number | null>(null)

  const handleRefreshNickname = async (record: WhitelistAccount) => {
    setRefreshingId(record.id)
    try {
      const r = await api.refreshWhitelistNickname(record.id)
      message.info(r.message)
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '刷新失败')
    } finally {
      setRefreshingId(null)
    }
  }

  const loadList = async () => {
    setLoading(true)
    try {
      const data = await api.getWhitelist({ is_active: isActive, search: search.trim() || undefined })
      setList(data.items)
    } catch {
      message.error('加载白名单失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadList()
  }, [isActive, search])

  const handleCreate = async () => {
    if (!newAccount.trim()) {
      message.error('请输入账号')
      return
    }
    try {
      await api.createWhitelistAccount({
        account: newAccount.trim(),
        remark: newRemark.trim() || undefined,
      })
      message.success('添加成功')
      setCreateOpen(false)
      setNewAccount('')
      setNewRemark('')
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '添加失败')
    }
  }

  const handleBatchCreate = async () => {
    const lines = batchText.split('\n').map(s => s.trim()).filter(Boolean)
    if (lines.length === 0) {
      message.error('请输入至少一个账号')
      return
    }
    setBatchLoading(true)
    try {
      const accounts = lines.map(account => ({ account }))
      const r = await api.batchCreateWhitelist(accounts)
      message.success(`批量添加完成：新增 ${r.created} 个，跳过 ${r.skipped} 个`)
      setBatchOpen(false)
      setBatchText('')
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '批量添加失败')
    } finally {
      setBatchLoading(false)
    }
  }

  const handleEdit = async () => {
    if (!editing) return
    try {
      await api.updateWhitelistAccount(editing.id, {
        nick_name: editNick.trim() || undefined,
        remark: editRemark.trim() || undefined,
        role: editRole,
      })
      message.success('修改成功')
      setEditOpen(false)
      setEditing(null)
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '修改失败')
    }
  }

  const handleToggle = async (record: WhitelistAccount) => {
    try {
      await api.updateWhitelistAccount(record.id, { is_active: record.is_active === 1 ? 0 : 1 })
      message.success(record.is_active === 1 ? '已禁用' : '已启用')
      loadList()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '操作失败')
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
    { title: '备注', dataIndex: 'remark', width: 220, render: (v: string | null) => v ?? '—' },
    {
      title: '角色', dataIndex: 'role', width: 90,
      render: (v: string) => v === 'super' ? <Tag color="purple">超管</Tag> : <Tag>管理员</Tag>,
    },
    {
      title: '状态', dataIndex: 'is_active', width: 90,
      render: (v: number) => v === 1 ? <Tag color="green">启用</Tag> : <Tag color="default">禁用</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', width: 180, render: (v: number) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '—' },
    {
      title: '操作', width: 190, fixed: 'right',
      render: (_: unknown, record: WhitelistAccount) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => {
            setEditing(record)
            setEditNick(record.nick_name ?? '')
            setEditRemark(record.remark ?? '')
            setEditRole(record.role ?? 'admin')
            setEditOpen(true)
          }} />
          <Tooltip title="获取昵称">
            <span>
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined spin={refreshingId === record.id} />}
                disabled={!!record.nick_name || refreshingId === record.id}
                onClick={() => handleRefreshNickname(record)}
              />
            </span>
          </Tooltip>
          <Tooltip title="白名单启用/禁用">
            <span>
              <Button
                type="text"
                size="small"
                icon={
                  record.is_active === 1
                    ? <CheckCircleOutlined style={{ color: '#16a34a' }} />
                    : <StopOutlined style={{ color: '#94a3b8' }} />
                }
                onClick={() => handleToggle(record)}
              />
            </span>
          </Tooltip>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => {
            setDeleting(record)
            setDeleteOpen(true)
          }} />
        </Space>
      ),
    },
  ]

  return (
    <div style={{ height: '100%', overflowY: 'auto', paddingRight: 4 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>人员管理</h2>
        <Space>
          <Input.Search
            allowClear
            placeholder="搜索账号/昵称"
            style={{ width: 220 }}
            onSearch={v => setSearch(v)}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 110 }}
            value={isActive}
            onChange={v => setIsActive(v)}
            options={[
              { value: 1, label: '启用' },
              { value: 0, label: '禁用' },
            ]}
          />
          <Button icon={<PlusOutlined />} onClick={() => setBatchOpen(true)}>批量添加</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>添加账号</Button>
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

      {/* 添加账号弹窗 */}
      <Modal
        title="添加账号"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); setNewAccount(''); setNewRemark('') }}
        onOk={handleCreate}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>账号 <span style={{ color: '#ef4444' }}>*</span></div>
          <Input
            value={newAccount}
            onChange={e => setNewAccount(e.target.value)}
            placeholder="请输入登录账号"
          />
        </div>
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>备注</div>
          <Input.TextArea value={newRemark} onChange={e => setNewRemark(e.target.value)} placeholder="请输入备注（选填）" autoSize={{ minRows: 2 }} />
        </div>
      </Modal>

      {/* 批量添加弹窗 */}
      <Modal
        title="批量添加账号"
        open={batchOpen}
        onCancel={() => { setBatchOpen(false); setBatchText('') }}
        onOk={handleBatchCreate}
        okText="添加"
        okButtonProps={{ loading: batchLoading }}
        cancelText="取消"
      >
        <div style={{ marginBottom: 8, fontWeight: 500 }}>账号列表（每行一个账号）</div>
        <Input.TextArea
          value={batchText}
          onChange={e => setBatchText(e.target.value)}
          placeholder={'admin\nzhangsan\nlisi'}
          autoSize={{ minRows: 6 }}
        />
        <div style={{ marginTop: 8, color: '#94a3b8', fontSize: 12 }}>昵称将自动从用户表带出（仅空时补充）。</div>
      </Modal>

      {/* 编辑账号弹窗 */}
      <Modal
        title="编辑账号"
        open={editOpen}
        onCancel={() => { setEditOpen(false); setEditing(null) }}
        onOk={handleEdit}
        okText="确定"
        cancelText="取消"
      >
        {editing && (
          <div style={{ marginBottom: 16, padding: '8px 12px', background: '#f8fafc', borderRadius: 6 }}>
            <span style={{ color: '#64748b', fontSize: 13 }}>账号: </span>
            <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{editing.account}</span>
          </div>
        )}
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>昵称</div>
          <Input value={editNick} onChange={e => setEditNick(e.target.value)} placeholder="请输入昵称（选填）" />
        </div>
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>角色</div>
          <Select
            value={editRole}
            onChange={setEditRole}
            style={{ width: '100%' }}
            options={[
              { value: 'super', label: '超管' },
              { value: 'admin', label: '管理员' },
            ]}
          />
        </div>
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>备注</div>
          <Input.TextArea value={editRemark} onChange={e => setEditRemark(e.target.value)} placeholder="请输入备注（选填）" autoSize={{ minRows: 2 }} />
        </div>
      </Modal>

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