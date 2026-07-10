import { useState, useRef } from 'react'
import { Button, Modal, Input, Select, Upload, message, Progress, Image } from 'antd'
import { UploadOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import type { RcFile } from 'antd/es/upload'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import { api } from '../api'

interface UploadItem {
  uid: string
  file: File | null
  thumbnail: File | null
  thumbnailPreview: string
  name: string
  description: string
  tags: string[]
}

interface Props {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

function BatchFileUploadModal({ open, onClose, onSuccess }: Props) {
  const [items, setItems] = useState<UploadItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleClose = () => {
    items.forEach(item => {
      if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
    })
    setItems([])
    setUploading(false)
    setUploadProgress(0)
    onClose()
  }

  const handleSelectFiles = (files: FileList | null) => {
    if (!files) return

    const newItems: UploadItem[] = Array.from(files).map(file => ({
      uid: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      thumbnail: null,
      thumbnailPreview: '',
      name: file.name.replace(/\.[^.]+$/, ''),
      description: '',
      tags: [],
    }))

    setItems(prev => [...prev, ...newItems])
  }

  const handleRemoveItem = (uid: string) => {
    const item = items.find(i => i.uid === uid)
    if (item?.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
    setItems(prev => prev.filter(i => i.uid !== uid))
  }

  const handleThumbnailChange = (uid: string, fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return

    const file = fileList[0]
    if (file.type !== 'image/png') {
      message.error('缩略图必须为 PNG 格式')
      return
    }

    const oldItem = items.find(i => i.uid === uid)
    if (oldItem?.thumbnailPreview) URL.revokeObjectURL(oldItem.thumbnailPreview)

    setItems(prev => prev.map(item =>
      item.uid === uid
        ? { ...item, thumbnail: file, thumbnailPreview: URL.createObjectURL(file) }
        : item
    ))
  }

  const updateItem = (uid: string, field: keyof UploadItem, value: string | string[]) => {
    setItems(prev => prev.map(item =>
      item.uid === uid ? { ...item, [field]: value } : item
    ))
  }

  const handleSubmit = async () => {
    const invalidItems = items.filter(item =>
      !item.file || !item.thumbnail || !item.name.trim()
    )

    if (invalidItems.length > 0) {
      message.error(`有 ${invalidItems.length} 个文件未完成（缺少文件、缩略图或名称）`)
      return
    }

    if (items.length === 0) {
      message.warning('请先添加文件')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const fd = new FormData()

      items.forEach(item => {
        if (item.file) fd.append('files', item.file)
      })

      items.forEach(item => {
        if (item.thumbnail) fd.append('thumbnails', item.thumbnail)
      })

      fd.append('items', JSON.stringify(items.map(item => ({
        name: item.name.trim(),
        description: item.description.trim(),
        tags: item.tags,
      }))))

      setUploadProgress(50)

      const res = await api.batchUploadFiles(fd)

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
      title="批量上传文件"
      open={open}
      onCancel={uploading ? undefined : handleClose}
      width={1000}
      footer={null}
      destroyOnClose
      maskClosable={!uploading}
    >
      <div style={{ marginBottom: 16 }}>
        <div style={{
          padding: '8px 12px',
          background: '#fff7ed',
          borderRadius: 6,
          color: '#c2410c',
          fontSize: 13,
          marginBottom: 12,
        }}>
          💡 每个文件必须选择对应的 PNG 缩略图，按顺序选择可避免错配
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={e => handleSelectFiles(e.target.files)}
        />

        {items.length > 0 && (
          <div style={{
            maxHeight: 500,
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
                <div style={{ width: 120, flexShrink: 0 }}>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                    文件
                  </div>
                  <div style={{ fontSize: 13, color: '#1e293b', fontWeight: 500 }}>
                    {item.file?.name || '—'}
                  </div>
                </div>

                <div style={{ width: 80, flexShrink: 0 }}>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                    缩略图
                  </div>
                  {item.thumbnailPreview ? (
                    <Image
                      src={item.thumbnailPreview}
                      width={48}
                      height={48}
                      style={{ borderRadius: 6, objectFit: 'cover' }}
                    />
                  ) : (
                    <label style={{ display: 'block' }}>
                      <input
                        type="file"
                        accept="image/png"
                        style={{ display: 'none' }}
                        onChange={e => handleThumbnailChange(item.uid, e.target.files)}
                        disabled={uploading}
                      />
                      <div style={{
                        width: 48,
                        height: 48,
                        background: '#fee2e2',
                        borderRadius: 6,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#ef4444',
                        fontSize: 20,
                        cursor: uploading ? 'not-allowed' : 'pointer',
                      }}>
                        +
                      </div>
                    </label>
                  )}
                </div>

                <Input
                  placeholder="名称"
                  value={item.name}
                  onChange={e => updateItem(item.uid, 'name', e.target.value)}
                  style={{ width: 140 }}
                  disabled={uploading}
                />

                <Input
                  placeholder="描述（可选）"
                  value={item.description}
                  onChange={e => updateItem(item.uid, 'description', e.target.value)}
                  style={{ flex: 1 }}
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
          添加文件
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
            {uploading ? '上传中...' : `提交 ${items.length} 个文件`}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default function FileManage() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <>
      <ResourceList
        type="file"
        label="文件"
        handleRef={listRef}
        extraActions={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setUploadModalOpen(true)}
          >
            批量上传
          </Button>
        }
      />
      <BatchFileUploadModal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={() => listRef.current?.refresh()}
      />
    </>
  )
}