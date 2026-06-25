import { useState, useEffect, useCallback } from 'react'
import { Form, Input, Button, Table, Tag, Image, Popconfirm, message, Typography, Space, Upload } from 'antd'
import { UploadOutlined, DeleteOutlined, PictureOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { RcFile } from 'antd/es/upload'
import { api } from '../api'
import type { Resource } from '../types'

export default function ImageManage() {
  const [form]     = Form.useForm()
  const [uploading, setUploading]   = useState(false)
  const [selected, setSelected]     = useState<RcFile | null>(null)
  const [preview, setPreview]       = useState<string | null>(null)
  const [items, setItems]           = useState<Resource[]>([])
  const [total, setTotal]           = useState(0)
  const [page, setPage]             = useState(1)
  const [loading, setLoading]       = useState(false)

  const fetchImages = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listResources({ type: 'image', page, limit: 20 })
      setItems(data.items); setTotal(data.total)
    } catch { message.error('加载图片列表失败') }
    finally { setLoading(false) }
  }, [page])

  useEffect(() => { fetchImages() }, [fetchImages])

  const handleUpload = async (v: { name: string; description?: string }) => {
    if (!selected) { message.warning('请先选择图片'); return }
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', selected)
      fd.append('name', v.name)
      if (v.description) fd.append('description', v.description)
      await api.uploadImage(fd)
      message.success('上传成功')
      form.resetFields(); setSelected(null); setPreview(null)
      if (page === 1) fetchImages(); else setPage(1)
    } catch { message.error('上传失败') }
    finally { setUploading(false) }
  }

  const handleDelete = async (id: number) => {
    try { await api.deleteResource(id); message.success('已删除'); fetchImages() }
    catch { message.error('删除失败') }
  }

  const columns: ColumnsType<Resource> = [
    {
      title: '图片',
      dataIndex: 'file_path',
      width: 72,
      render: (v: string | null) =>
        v ? (
          <Image
            width={48} height={48}
            src={`/static/${v}`}
            style={{ objectFit: 'cover', borderRadius: 8, border: '1px solid #e2e8f0' }}
            preview={{ src: `/static/${v}` }}
          />
        ) : (
          <div style={{
            width: 48, height: 48, borderRadius: 8,
            background: '#f8fafc', border: '1px solid #e2e8f0',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e1',
          }}>
            <PictureOutlined />
          </div>
        ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      render: (name: string) => <span style={{ fontWeight: 500, color: '#0f172a' }}>{name}</span>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (v: string | null) => v ?? <span style={{ color: '#cbd5e1' }}>—</span>,
    },
    {
      title: '尺寸',
      dataIndex: 'dimensions',
      width: 110,
      render: (v: { width: number; height: number } | null) =>
        v ? <span style={{ fontSize: 12, color: '#64748b', fontFamily: 'ui-monospace, monospace' }}>{v.width}×{v.height}</span> : '—',
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      width: 80,
      render: (v: number | null) =>
        v ? <span style={{ fontSize: 12, color: '#64748b' }}>{(v / 1024).toFixed(1)} KB</span> : '—',
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
      width: 60, align: 'right' as const,
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
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>图片管理</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>上传并管理图片资源</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Upload form */}
        <div style={{
          background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0',
          padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}>
          <Typography.Title level={5} style={{ margin: '0 0 20px', color: '#0f172a' }}>上传图片</Typography.Title>
          <Form form={form} layout="vertical" onFinish={handleUpload}>
            <Form.Item name="name" label={<span style={{ fontWeight: 500, fontSize: 13 }}>图片名称</span>} rules={[{ required: true }]}>
              <Input placeholder="请输入图片名称" size="large" />
            </Form.Item>
            <Form.Item name="description" label={<span style={{ fontWeight: 500, fontSize: 13 }}>描述</span>}>
              <Input.TextArea rows={2} placeholder="可选" />
            </Form.Item>

            {/* File picker */}
            <Form.Item label={<span style={{ fontWeight: 500, fontSize: 13 }}>图片文件</span>} required>
              <Upload
                accept="image/*"
                maxCount={1}
                fileList={selected ? [{ uid: '-1', name: selected.name, status: 'done' } as never] : []}
                beforeUpload={file => {
                  setSelected(file)
                  setPreview(URL.createObjectURL(file))
                  return false
                }}
                onRemove={() => { setSelected(null); setPreview(null) }}
              >
                <Button icon={<UploadOutlined />}>选择图片</Button>
              </Upload>

              {/* Preview */}
              {preview && (
                <div style={{ marginTop: 12 }}>
                  <img
                    src={preview}
                    alt="preview"
                    style={{
                      width: '100%', maxHeight: 160, objectFit: 'cover',
                      borderRadius: 10, border: '1px solid #e2e8f0',
                    }}
                  />
                </div>
              )}
            </Form.Item>

            <Button
              type="primary"
              htmlType="submit"
              loading={uploading}
              disabled={!selected}
              icon={<UploadOutlined />}
              block size="large"
            >
              上传图片
            </Button>
          </Form>
        </div>

        {/* List */}
        <div style={{
          background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0',
          overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
        }}>
          <div style={{ padding: '18px 20px 14px', borderBottom: '1px solid #f1f5f9' }}>
            <Typography.Title level={5} style={{ margin: 0, color: '#0f172a' }}>
              已上传图片 <span style={{ fontSize: 13, fontWeight: 400, color: '#94a3b8' }}>({total})</span>
            </Typography.Title>
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
            locale={{ emptyText: <div style={{ padding: '40px 0', color: '#cbd5e1' }}>暂无图片</div> }}
          />
        </div>
      </div>
    </div>
  )
}
