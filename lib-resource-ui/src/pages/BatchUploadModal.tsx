import { useState, useRef } from 'react'
import { Modal, Button, Input, Select, Upload, message, Progress, Image } from 'antd'
import { UploadOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import type { RcFile } from 'antd/es/upload'
import { api } from '../api'

interface UploadItem {
  uid: string
  file: File | null
  preview: string
  name: string
  description: string
  tags: string[]
}

interface Props {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function BatchUploadModal({ open, onClose, onSuccess }: Props) {
  const [items, setItems] = useState<UploadItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleClose = () => {
    items.forEach(item => {
      if (item.preview) URL.revokeObjectURL(item.preview)
    })
    setItems([])
    setUploading(false)
    setUploadProgress(0)
    onClose()
  }

  const handleSelectFiles = (files: FileList | null) => {
    if (!files) return
    
    const ALLOWED_TYPES = ['png', 'svg', 'jpeg', 'jpg', 'webp']
    const ALLOWED_MIME_TYPES = ['image/png', 'image/svg+xml', 'image/jpeg', 'image/webp']
    
    const validFiles = Array.from(files).filter(file => {
      const ext = file.name.split('.').pop()?.toLowerCase() || ''
      const mime = file.type
      return ALLOWED_TYPES.includes(ext) && ALLOWED_MIME_TYPES.includes(mime)
    })
    
    if (validFiles.length < files.length) {
      message.warning(`已过滤 ${files.length - validFiles.length} 个不支持的文件类型（仅支持 png/svg/jpeg/webp）`)
    }
    
    if (validFiles.length === 0) return
    
    const newItems: UploadItem[] = validFiles.map(file => ({
      uid: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      preview: URL.createObjectURL(file),
      name: file.name.replace(/\.[^.]+$/, ''),
      description: '',
      tags: [],
    }))
    setItems(prev => [...prev, ...newItems])
  }

  const handleRemoveItem = (uid: string) => {
    const item = items.find(i => i.uid === uid)
    if (item?.preview) URL.revokeObjectURL(item.preview)
    setItems(prev => prev.filter(i => i.uid !== uid))
  }

  const updateItem = (uid: string, field: keyof UploadItem, value: string | string[]) => {
    setItems(prev => prev.map(item =>
      item.uid === uid ? { ...item, [field]: value } : item
    ))
  }

  const handleSubmit = async () => {
    const invalid = items.filter(item => !item.file || !item.name.trim())
    if (invalid.length > 0) {
      message.error('请确保所有图片都已选择文件并填写名称')
      return
    }

    if (items.length === 0) {
      message.warning('请先添加图片')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const fd = new FormData()
      items.forEach(item => {
        if (item.file) fd.append('files', item.file)
      })
      fd.append('items', JSON.stringify(items.map(item => ({
        name: item.name.trim(),
        description: item.description.trim(),
        tags: item.tags,
      }))))

      setUploadProgress(50)

      const res = await api.batchUploadImages(fd)

      setUploadProgress(100)
      message.success(res.message)
      onSuccess()
      handleClose()
    } catch (e: unknown) {
      message.error('上传失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <Modal
      title="批量上传图片"
      open={open}
      onCancel={uploading ? undefined : handleClose}
      width={750}
      footer={null}
      destroyOnClose
      maskClosable={!uploading}
    >
      <div style={{ marginBottom: 16 }}>
        <div style={{
          padding: '8px 12px',
          background: '#f0f9ff',
          borderRadius: 6,
          color: '#0369a1',
          fontSize: 13,
          marginBottom: 12,
        }}>
          💡 建议单次上传不超过 50 张图片
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/svg+xml,image/jpeg,image/webp"
          multiple
          style={{ display: 'none' }}
          onChange={e => handleSelectFiles(e.target.files)}
        />

        {items.length > 0 && (
          <div style={{
            maxHeight: 400,
            overflowY: 'auto',
            border: '1px solid #e2e8f0',
            borderRadius: 8,
          }}>
            {items.map(item => (
              <div
                key={item.uid}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 16px',
                  borderBottom: '1px solid #f1f5f9',
                }}
              >
                <div style={{ width: 64, height: 64, flexShrink: 0 }}>
                  {item.preview ? (
                    <Image
                      src={item.preview}
                      width={64}
                      height={64}
                      style={{ borderRadius: 6, objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{
                      width: 64, height: 64,
                      background: '#f8fafc',
                      borderRadius: 6,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#cbd5e1',
                      fontSize: 20,
                    }}>
                      📷
                    </div>
                  )}
                </div>

                <Input
                  placeholder="图片名称"
                  value={item.name}
                  onChange={e => updateItem(item.uid, 'name', e.target.value)}
                  style={{ width: 140 }}
                  disabled={uploading}
                />

                <Input
                  placeholder="描述（可选）"
                  value={item.description}
                  onChange={e => updateItem(item.uid, 'description', e.target.value)}
                  style={{ width: 200 }}
                  disabled={uploading}
                />

                <Select
                  mode="tags"
                  placeholder="标签"
                  value={item.tags}
                  onChange={val => updateItem(item.uid, 'tags', val)}
                  style={{ width: 150 }}
                  size="small"
                  tokenSeparators={[',']}
                  disabled={uploading}
                />

                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleRemoveItem(item.uid)}
                  disabled={uploading}
                />
              </div>
            ))}
          </div>
        )}

        <Button
          icon={<PlusOutlined />}
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          style={{ marginTop: 12 }}
        >
          添加图片
        </Button>

        {uploading && (
          <div style={{ marginTop: 16 }}>
            <Progress
              percent={uploadProgress}
              status="active"
              format={() => `上传进度：${uploadProgress}%`}
            />
          </div>
        )}

        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 8,
          marginTop: 16,
          paddingTop: 16,
          borderTop: '1px solid #f1f5f9',
        }}>
          <Button onClick={handleClose} disabled={uploading}>
            取消
          </Button>
          <Button
            type="primary"
            onClick={handleSubmit}
            loading={uploading}
            disabled={items.length === 0}
          >
            {uploading ? '上传中...' : `提交 ${items.length} 张`}
          </Button>
        </div>
      </div>
    </Modal>
  )
}