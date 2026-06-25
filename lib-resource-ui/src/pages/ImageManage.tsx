import { useState, useRef } from 'react'
import { Button, Modal, Form, Input, Upload, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import type { RcFile } from 'antd/es/upload'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import { api } from '../api'

function UploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [form] = Form.useForm()
  const [uploading, setUploading] = useState(false)
  const [selected, setSelected] = useState<RcFile | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  const handleClose = () => {
    form.resetFields()
    setSelected(null)
    setPreview(null)
    onClose()
  }

  const handleSubmit = async () => {
    if (!selected) { message.warning('请先选择图片'); return }
    const values = await form.validateFields()
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', selected)
      fd.append('name', values.name)
      if (values.description) fd.append('description', values.description)
      await api.uploadImage(fd)
      message.success('上传成功')
      handleClose()
    } catch { message.error('上传失败') }
    finally { setUploading(false) }
  }

  return (
    <Modal
      title="上传图片"
      open={open}
      onOk={handleSubmit}
      onCancel={handleClose}
      okText="上传"
      cancelText="取消"
      confirmLoading={uploading}
      okButtonProps={{ disabled: !selected }}
      destroyOnClose
      width={480}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="name" label="图片名称" rules={[{ required: true }]}>
          <Input placeholder="请输入图片名称" />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <Input.TextArea rows={2} placeholder="可选" />
        </Form.Item>
        <Form.Item label="图片文件" required>
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
          {preview && (
            <img
              src={preview}
              alt="preview"
              style={{
                marginTop: 12, width: '100%', maxHeight: 160,
                objectFit: 'cover', borderRadius: 10, border: '1px solid #e2e8f0',
              }}
            />
          )}
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default function ImageManage() {
  const [modalOpen, setModalOpen] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <>
      <ResourceList
        type="image"
        label="图片"
        handleRef={listRef}
        extraActions={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setModalOpen(true)}
          >
            上传图片
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
