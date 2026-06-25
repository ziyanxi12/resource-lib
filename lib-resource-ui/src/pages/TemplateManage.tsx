import { useState, useEffect, useCallback } from 'react'
import { Form, Input, Button, Table, Tag, Popconfirm, message, Typography, Space } from 'antd'
import { UploadOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { api } from '../api'
import type { Resource } from '../types'

export default function TemplateManage() {
  const [form]      = Form.useForm()
  const [uploading, setUploading] = useState(false)
  const [items, setItems]         = useState<Resource[]>([])
  const [total, setTotal]         = useState(0)
  const [page, setPage]           = useState(1)
  const [loading, setLoading]     = useState(false)

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listResources({ type: 'template', page, limit: 20 })
      setItems(data.items); setTotal(data.total)
    } catch { message.error('加载模版列表失败') }
    finally { setLoading(false) }
  }, [page])

  useEffect(() => { fetchTemplates() }, [fetchTemplates])

  const handleUpload = async (v: { name: string; description?: string; hex_data: string }) => {
    setUploading(true)
    try {
      await api.uploadTemplate({ name: v.name, description: v.description, hex_data: v.hex_data })
      message.success('上传成功')
      form.resetFields()
      if (page === 1) fetchTemplates(); else setPage(1)
    } catch { message.error('上传失败') }
    finally { setUploading(false) }
  }

  const handleDelete = async (id: number) => {
    try { await api.deleteResource(id); message.success('已删除'); fetchTemplates() }
    catch { message.error('删除失败') }
  }

  const columns: ColumnsType<Resource> = [
    {
      title: '模版名称',
      dataIndex: 'name',
      render: (name: string) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: '#f5f3ff', color: '#7c3aed',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14, flexShrink: 0,
          }}>
            <FileTextOutlined />
          </div>
          <span style={{ fontWeight: 500, color: '#0f172a' }}>{name}</span>
        </div>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string | null) => v ?? <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      render: (tags: string[]) =>
        tags.length
          ? <Space size={4} wrap>{tags.map(t => <Tag key={t} style={{ margin: 0, borderRadius: 4 }}>{t}</Tag>)}</Space>
          : <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 148,
      render: (v: string | null) => <span style={{ fontSize: 12, color: '#94a3b8' }}>{v ? v.slice(0, 19).replace('T', ' ') : '—'}</span>,
    },
    {
      title: '',
      width: 60,
      align: 'right' as const,
      render: (_: unknown, r: Resource) => (
        <Popconfirm title="确认删除？" okText="删除" okButtonProps={{ danger: true }} onConfirm={() => handleDelete(r.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>模版管理</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>上传模版 hex 数据并管理已有模版</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 20, alignItems: 'start' }}>
        {/* Upload form */}
        <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <Typography.Title level={5} style={{ margin: '0 0 20px', color: '#0f172a' }}>上传新模版</Typography.Title>
          <Form form={form} layout="vertical" onFinish={handleUpload}>
            <Form.Item name="name" label={<span style={{ fontWeight: 500, fontSize: 13 }}>模版名称</span>} rules={[{ required: true, message: '请输入名称' }]}>
              <Input placeholder="请输入模版名称" size="large" />
            </Form.Item>
            <Form.Item name="description" label={<span style={{ fontWeight: 500, fontSize: 13 }}>描述</span>}>
              <Input.TextArea rows={2} placeholder="可选" />
            </Form.Item>
            <Form.Item name="hex_data" label={<span style={{ fontWeight: 500, fontSize: 13 }}>Hex 数据</span>} rules={[{ required: true, message: '请粘贴 hex 数据' }]}>
              <Input.TextArea
                rows={8}
                placeholder="粘贴 hex 数据…"
                style={{ fontFamily: 'ui-monospace, SFMono-Regular, monospace', fontSize: 12, background: '#f8fafc' }}
              />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" loading={uploading} icon={<UploadOutlined />} block size="large">
                上传模版
              </Button>
            </Form.Item>
          </Form>
        </div>

        {/* List */}
        <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <div style={{ padding: '18px 20px 14px', borderBottom: '1px solid #f1f5f9' }}>
            <Typography.Title level={5} style={{ margin: 0, color: '#0f172a' }}>已上传模版</Typography.Title>
          </div>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={items}
            loading={loading}
            size="middle"
            style={{ borderRadius: 0 }}
            pagination={{
              current: page, pageSize: 20, total,
              onChange: setPage, showSizeChanger: false,
              showTotal: t => `共 ${t} 条`,
              style: { padding: '12px 20px' },
            }}
            locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无模版</div> }}
          />
        </div>
      </div>
    </div>
  )
}
