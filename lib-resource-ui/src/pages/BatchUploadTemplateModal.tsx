import { useState, useRef } from 'react'
import { Modal, Button, Input, Select, message, Progress, Image } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { api } from '../api'

interface UploadTemplateItem {
  uid: string
  previewFile: File | null
  previewUrl: string
  hexData: string
  name: string
  description: string
  tags: string[]
}

interface Props {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

const ALLOWED_PREVIEW_TYPES = ['png']
const ALLOWED_PREVIEW_MIME_TYPES = ['image/png']

export default function BatchUploadTemplateModal({ open, onClose, onSuccess }: Props) {
  const [items, setItems] = useState<UploadTemplateItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const previewInputRef = useRef<HTMLInputElement>(null)
  const currentUidRef = useRef<string>('')

  const handleClose = () => {
    items.forEach(item => {
      if (item.previewUrl) URL.revokeObjectURL(item.previewUrl)
    })
    setItems([])
    setUploading(false)
    setUploadProgress(0)
    onClose()
  }

  const handleAddTemplate = () => {
    const newItem: UploadTemplateItem = {
      uid: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      previewFile: null,
      previewUrl: '',
      hexData: '',
      name: '',
      description: '',
      tags: [],
    }
    setItems(prev => [...prev, newItem])
  }

  const handleSelectPreview = (uid: string) => {
    currentUidRef.current = uid
    previewInputRef.current?.click()
  }

  const handlePreviewChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    
    const file = files[0]
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    const mime = file.type
    
    if (!ALLOWED_PREVIEW_TYPES.includes(ext) || !ALLOWED_PREVIEW_MIME_TYPES.includes(mime)) {
      message.error('预览图仅支持 png 格式')
      return
    }
    
    const uid = currentUidRef.current
    updateItem(uid, 'previewFile', file)
    updateItem(uid, 'previewUrl', URL.createObjectURL(file))
    
    e.target.value = ''
  }

  const handleRemoveItem = (uid: string) => {
    const item = items.find(i => i.uid === uid)
    if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl)
    setItems(prev => prev.filter(i => i.uid !== uid))
  }

  const updateItem = (uid: string, field: keyof UploadTemplateItem, value: File | string | string[]) => {
    setItems(prev => prev.map(item =>
      item.uid === uid ? { ...item, [field]: value } : item
    ))
  }

  const handleSubmit = async () => {
    // 检查缩略图
    const missingPreview = items.filter(item => !item.previewFile)
    if (missingPreview.length > 0) {
      message.error(`请为所有模版上传缩略图（PNG格式）`)
      return
    }
    
    // 检查名称
    const missingName = items.filter(item => !item.name.trim())
    if (missingName.length > 0) {
      message.error('请填写所有模版的名称')
      return
    }
    
    // 检查 hex 数据
    const missingHex = items.filter(item => !item.hexData.trim())
    if (missingHex.length > 0) {
      message.error('请填写所有模版的 hex 数据')
      return
    }

    if (items.length === 0) {
      message.warning('请先添加模版')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const fd = new FormData()
      items.forEach(item => {
        if (item.previewFile) fd.append('preview_files', item.previewFile)
      })
      fd.append('hex_datas', JSON.stringify(items.map(item => item.hexData.trim())))
      fd.append('items', JSON.stringify(items.map(item => ({
        name: item.name.trim(),
        description: item.description.trim(),
        tags: item.tags,
      }))))

      setUploadProgress(50)

      const res = await api.batchUploadTemplates(fd)

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
      title="批量上传模版"
      open={open}
      onCancel={uploading ? undefined : handleClose}
      width={800}
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
          💡 建议单次上传不超过 20 个模版
        </div>

        <input
          ref={previewInputRef}
          type="file"
          accept="image/png"
          style={{ display: 'none' }}
          onChange={handlePreviewChange}
        />

        {items.length > 0 && (
          <div style={{
            maxHeight: 450,
            overflowY: 'auto',
            border: '1px solid #e2e8f0',
            borderRadius: 8,
          }}>
            {/* 表头行 */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 16px',
              background: '#f8fafc',
              fontWeight: 600,
              fontSize: 13,
              color: '#475569',
              borderBottom: '1px solid #e2e8f0',
            }}>
              <div style={{ width: 64, textAlign: 'center', flexShrink: 0 }}>缩略图</div>
              <div style={{ width: 120, flexShrink: 0 }}>名称</div>
              <div style={{ width: 120, flexShrink: 0 }}>描述</div>
              <div style={{ flex: 1, minWidth: 200 }}>Hex 数据</div>
              <div style={{ width: 120, flexShrink: 0 }}>标签</div>
              <div style={{ width: 32, flexShrink: 0 }}>操作</div>
            </div>
            
            {items.map(item => (
              <div
                key={item.uid}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  padding: '12px 16px',
                  borderBottom: '1px solid #f1f5f9',
                }}
              >
                <div 
                  style={{ 
                    width: 64, 
                    height: 64, 
                    flexShrink: 0,
                    cursor: 'pointer',
                    position: 'relative',
                  }}
                  onClick={() => !uploading && handleSelectPreview(item.uid)}
                >
                  {item.previewUrl ? (
                    <Image
                      src={item.previewUrl}
                      width={64}
                      height={64}
                      style={{ borderRadius: 6, objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{
                      width: 64, height: 64,
                      background: '#f8fafc',
                      borderRadius: 6,
                      border: '1px dashed #e2e8f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#94a3b8',
                      fontSize: 11,
                      flexDirection: 'column',
                      gap: 4,
                    }}>
                      <span style={{ fontSize: 20 }}>📷</span>
                      <span>选择 PNG</span>
                    </div>
                  )}
                </div>

                <Input
                  placeholder="模版名称"
                  value={item.name}
                  onChange={e => updateItem(item.uid, 'name', e.target.value)}
                  style={{ width: 120 }}
                  disabled={uploading}
                />

                <Input
                  placeholder="描述（可选）"
                  value={item.description}
                  onChange={e => updateItem(item.uid, 'description', e.target.value)}
                  style={{ width: 120 }}
                  disabled={uploading}
                />

                <Input.TextArea
                  placeholder="粘贴 hex 数据"
                  value={item.hexData}
                  onChange={e => updateItem(item.uid, 'hexData', e.target.value)}
                  style={{ 
                    width: 280,
                    fontFamily: 'ui-monospace,monospace', 
                    fontSize: 11, 
                    background: '#f8fafc' 
                  }}
                  rows={3}
                  disabled={uploading}
                />

                <Select
                  mode="tags"
                  placeholder="标签"
                  value={item.tags}
                  onChange={val => updateItem(item.uid, 'tags', val)}
                  style={{ width: 120 }}
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
          onClick={handleAddTemplate}
          disabled={uploading}
          style={{ marginTop: 12 }}
        >
          添加模版
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
            {uploading ? '上传中...' : `提交 ${items.length} 个`}
          </Button>
        </div>
      </div>
    </Modal>
  )
}