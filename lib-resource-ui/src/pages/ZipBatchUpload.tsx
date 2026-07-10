import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Upload, Table, Input, Select, message, Progress, Image, Tag } from 'antd'
import { ArrowLeftOutlined, UploadOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons'
import type { RcFile } from 'antd/es/upload'
import JSZip from 'jszip'
import { api } from '../api'

interface PreviewItem {
  index: number
  name: string
  description: string
  tags: string[]
  file: File | null
  thumbnail: File | null
  thumbnailPreview: string
  file_path: string
  thumbnail_path: string
  file_exists: boolean
  thumbnail_exists: boolean
  valid: boolean
  error: string | null
}

export default function ZipBatchUpload() {
  const navigate = useNavigate()
  const [items, setItems] = useState<PreviewItem[]>([])
  const [selectedRows, setSelectedRows] = useState<number[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const handleUploadZip = async (zipFile: RcFile) => {
    try {
      message.loading({ content: '解析 ZIP 文件...', key: 'parse' })

      if (zipFile.size > 50 * 1024 * 1024) {
        message.error({ content: 'ZIP 文件过大，建议不超过 50MB', key: 'parse' })
        return
      }

      const zip = await JSZip.loadAsync(zipFile)

      const configFile = zip.file('config.json')
      if (!configFile) {
        message.error({ content: 'ZIP 缺少 config.json 配置文件（必须位于根目录）', key: 'parse' })
        return
      }

      const configStr = await configFile.async('text')
      let config: any
      try {
        config = JSON.parse(configStr)
      } catch (e) {
        message.error({ content: 'config.json 格式错误', key: 'parse' })
        return
      }

      const meta = config.meta || {}
      if (meta.type !== 'file') {
        message.error({ content: `不支持类型 '${meta.type}'，仅支持 file`, key: 'parse' })
        return
      }

      const dataItems = config.data || []
      if (!Array.isArray(dataItems) || dataItems.length === 0) {
        message.error({ content: 'data 必须为非空数组', key: 'parse' })
        return
      }

      const previewItems: PreviewItem[] = []
      const filePathSet = new Set<string>()

      for (let idx = 0; idx < dataItems.length; idx++) {
        const item = dataItems[idx]
        const name = item.name?.trim() || ''
        const filePath = item.file_path?.trim() || ''
        const thumbnailPath = item.thumbnail_path?.trim() || ''

        if (!name) {
          previewItems.push({
            index: idx,
            name: '',
            description: item.description || '',
            tags: item.tags || [],
            file: null,
            thumbnail: null,
            thumbnailPreview: '',
            file_path: filePath,
            thumbnail_path: thumbnailPath,
            file_exists: false,
            thumbnail_exists: false,
            valid: false,
            error: '名称不能为空',
          })
          continue
        }

        if (filePathSet.has(filePath)) {
          previewItems.push({
            index: idx,
            name,
            description: item.description || '',
            tags: item.tags || [],
            file: null,
            thumbnail: null,
            thumbnailPreview: '',
            file_path: filePath,
            thumbnail_path: thumbnailPath,
            file_exists: false,
            thumbnail_exists: false,
            valid: false,
            error: '文件路径重复',
          })
          continue
        }

        filePathSet.add(filePath)

        const fileZipObj = zip.file(filePath)
        const fileExists = !!fileZipObj

        const thumbnailZipObj = zip.file(thumbnailPath)
        const thumbnailExists = !!thumbnailZipObj

        let fileObj: File | null = null
        if (fileExists) {
          const fileBlob = await fileZipObj.async('blob')
          const fileName = filePath.split('/').pop() || 'file'
          fileObj = new File([fileBlob], fileName)
        }

        let thumbnailObj: File | null = null
        let thumbnailPreviewUrl = ''
        if (thumbnailExists) {
          const thumbnailBlob = await thumbnailZipObj.async('blob')
          const thumbName = thumbnailPath.split('/').pop() || 'thumbnail.png'
          thumbnailObj = new File([thumbnailBlob], thumbName, { type: 'image/png' })
          thumbnailPreviewUrl = URL.createObjectURL(thumbnailBlob)
        }

        const isValid = fileExists && thumbnailExists
        const error = !fileExists ? '文件不存在' : !thumbnailExists ? '缩略图不存在' : null

        previewItems.push({
          index: idx,
          name,
          description: item.description || '',
          tags: item.tags || [],
          file: fileObj,
          thumbnail: thumbnailObj,
          thumbnailPreview: thumbnailPreviewUrl,
          file_path: filePath,
          thumbnail_path: thumbnailPath,
          file_exists: fileExists,
          thumbnail_exists: thumbnailExists,
          valid: isValid,
          error,
        })
      }

      message.success({
        content: `解析成功：共 ${dataItems.length} 个文件，有效 ${previewItems.filter(i => i.valid).length} 个`,
        key: 'parse'
      })

      setItems(previewItems)
      setSelectedRows(previewItems.filter(i => i.valid).map(i => i.index))
    } catch (e: unknown) {
      message.error({ content: '解析失败：' + (e instanceof Error ? e.message : '未知错误'), key: 'parse' })
    }
  }

  const handleConfirmUpload = async () => {
    const validItems = items.filter(i => selectedRows.includes(i.index) && i.valid)
    if (validItems.length === 0) {
      message.error('请选择至少一个有效文件')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const fd = new FormData()

      validItems.forEach(item => {
        if (item.file) fd.append('files', item.file)
      })

      validItems.forEach(item => {
        if (item.thumbnail) fd.append('thumbnails', item.thumbnail)
      })

      fd.append('items', JSON.stringify(validItems.map(item => ({
        name: item.name.trim(),
        description: item.description.trim(),
        tags: item.tags,
      }))))

      setUploadProgress(50)

      const res = await api.batchUploadFiles(fd)

      setUploadProgress(100)
      message.success(res.message)

      items.forEach(item => {
        if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
      })

      navigate('/file')
    } catch (e: unknown) {
      message.error('上传失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const updateItem = (index: number, field: string, value: any) => {
    setItems(prev => prev.map(item =>
      item.index === index ? { ...item, [field]: value } : item
    ))
  }

  const handleRemoveItem = (index: number) => {
    const item = items.find(i => i.index === index)
    if (item?.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)

    setItems(prev => prev.filter(i => i.index !== index))
    setSelectedRows(prev => prev.filter(i => i !== index))
  }

  const handleBack = () => {
    items.forEach(item => {
      if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
    })
    navigate('/file')
  }

  const columns = [
    {
      title: '状态',
      dataIndex: 'valid',
      width: 120,
      render: (valid: boolean, record: PreviewItem) => (
        valid ? <Tag color="green">有效</Tag> : <Tag color="red">{record.error || '无效'}</Tag>
      ),
    },
    {
      title: '序号',
      dataIndex: 'index',
      width: 60,
      render: (idx: number) => idx + 1,
    },
    {
      title: '缩略图',
      dataIndex: 'thumbnailPreview',
      width: 100,
      render: (preview: string, record: PreviewItem) => (
        preview ? (
          <Image
            src={preview}
            width={64}
            height={64}
            style={{ borderRadius: 6, objectFit: 'cover' }}
          />
        ) : (
          <div style={{
            width: 64, height: 64,
            background: '#fee2e2',
            borderRadius: 6,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#ef4444',
            fontSize: 12,
          }}>
            无缩略图
          </div>
        )
      ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 180,
      render: (name: string, record: PreviewItem) => (
        <Input
          value={name}
          onChange={e => updateItem(record.index, 'name', e.target.value)}
          disabled={!record.valid || uploading}
          placeholder="名称"
        />
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: 200,
      render: (desc: string, record: PreviewItem) => (
        <Input
          value={desc}
          onChange={e => updateItem(record.index, 'description', e.target.value)}
          disabled={!record.valid || uploading}
          placeholder="描述（可选）"
        />
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 150,
      render: (tags: string[], record: PreviewItem) => (
        <Select
          mode="tags"
          value={tags}
          onChange={val => updateItem(record.index, 'tags', val)}
          disabled={!record.valid || uploading}
          placeholder="标签"
          tokenSeparators={[',']}
        />
      ),
    },
    {
      title: '文件路径',
      dataIndex: 'file_path',
      width: 180,
      ellipsis: true,
    },
    {
      title: '文件大小',
      dataIndex: 'file',
      width: 100,
      render: (file: File | null) => file ? `${(file.size / 1024).toFixed(1)} KB` : '-',
    },
    {
      title: '操作',
      width: 80,
      render: (_: any, record: PreviewItem) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleRemoveItem(record.index)}
          disabled={uploading}
        />
      ),
    },
  ]

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        marginBottom: 20,
        paddingBottom: 16,
        borderBottom: '1px solid #e2e8f0',
      }}>
        <Button icon={<ArrowLeftOutlined />} onClick={handleBack} disabled={uploading}>
          返回
        </Button>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: '#1e293b' }}>
          ZIP 批量上传文件
        </h2>
      </div>

      {items.length === 0 && (
        <div style={{ padding: 24, textAlign: 'center' }}>
          <div style={{ marginBottom: 16 }}>
            <Button
              type="link"
              icon={<DownloadOutlined />}
              href="/example_batch_upload.zip"
              download
            >
              下载示例 ZIP
            </Button>
          </div>

          <Upload.Dragger
            accept=".zip"
            beforeUpload={handleUploadZip}
            showUploadList={false}
            disabled={uploading}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽 ZIP 文件到此区域</p>
            <p className="ant-upload-hint">
              ZIP 必须包含 config.json（位于根目录）和对应的文件 + PNG 缩略图<br/>
              建议 ZIP 文件不超过 50MB
            </p>
          </Upload.Dragger>
        </div>
      )}

      {items.length > 0 && (
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{
            padding: '8px 12px',
            background: '#fff7ed',
            borderRadius: 6,
            color: '#c2410c',
            fontSize: 13,
            marginBottom: 12,
          }}>
            共 {items.length} 个文件，有效 {items.filter(i => i.valid).length} 个，已选择 {selectedRows.length} 个
          </div>

          <div style={{ flex: 1, overflow: 'auto' }}>
            <Table
              rowKey="index"
              columns={columns}
              dataSource={items}
              rowSelection={{
                selectedRowKeys: selectedRows,
                onChange: keys => setSelectedRows(keys as number[]),
                getCheckboxProps: record => ({ disabled: !record.valid }),
              }}
              pagination={false}
              size="small"
            />
          </div>
        </div>
      )}

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
        <Button onClick={handleBack} disabled={uploading}>
          取消
        </Button>
        <Button
          type="primary"
          onClick={handleConfirmUpload}
          loading={uploading}
          disabled={items.length === 0 || selectedRows.length === 0}
        >
          {uploading ? '上传中...' : `提交 ${selectedRows.length} 个文件`}
        </Button>
      </div>
    </div>
  )
}