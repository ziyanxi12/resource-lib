import { useState, useRef } from 'react'
import { Button, Modal, Form, Input, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import { api } from '../api'

function UploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [form] = Form.useForm()
  const [uploading, setUploading] = useState(false)

  const handleSubmit = async () => {
    const values = await form.validateFields()
    setUploading(true)
    try {
      await api.uploadTemplate({ name: values.name, description: values.description, hex_data: values.hex_data })
      message.success('上传成功')
      form.resetFields()
      onClose()
    } catch { message.error('上传失败') }
    finally { setUploading(false) }
  }

  return (
    <Modal
      title="上传模版"
      open={open}
      onOk={handleSubmit}
      onCancel={() => { form.resetFields(); onClose() }}
      okText="上传"
      cancelText="取消"
      confirmLoading={uploading}
      destroyOnClose
      width={520}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="name" label="模版名称" rules={[{ required: true, message: '请输入名称' }]}>
          <Input placeholder="请输入模版名称" />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <Input.TextArea rows={2} placeholder="可选" />
        </Form.Item>
        <Form.Item name="hex_data" label="Hex 数据" rules={[{ required: true, message: '请粘贴 hex 数据' }]}>
          <Input.TextArea
            rows={8}
            placeholder="粘贴 hex 数据…"
            style={{ fontFamily: 'ui-monospace,monospace', fontSize: 12, background: '#f8fafc' }}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default function TemplateManage() {
  const [modalOpen, setModalOpen] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <>
      <ResourceList
        type="template"
        label="模版"
        handleRef={listRef}
        extraActions={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setModalOpen(true)}
          >
            上传模版
          </Button>
        }
      />
      <UploadModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          listRef.current?.refresh()
        }}
      />
    </>
  )
}
