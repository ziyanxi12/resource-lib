import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Input, Select, message, Progress, Image, InputNumber, Tooltip, Upload, TreeSelect } from 'antd'
import { ArrowLeftOutlined, DeleteOutlined, FileZipOutlined, PlusOutlined, UploadOutlined } from '@ant-design/icons'
import JSZip from 'jszip'
import { api, Source, GroupNode } from '../api'

interface ZipItem {
  uid: string
  name: string
  description: string
  group_id: number | null
  tags: string[]
  search_text: string
  width: number
  height: number
  file_path: string
  file_url: string
  thumbnail_path: string
  thumbnailPreview: string
  raw_data: Record<string, unknown>
  raw_data_string: string
  fileBlob: Blob | null
  thumbnailBlob: Blob | null
  errors: Record<string, string>
}

const RESOURCE_TYPE_MAP: Record<string, number> = {
  component: 1,
  template: 2,
  image: 5,
  file: 6,
  icon: 3,
  illus: 4,
}

const TYPE_LABELS: Record<string, string> = {
  component: '组件',
  template: '模版',
  image: '图片',
  file: '文件',
  icon: '图标',
  illus: '插画',
}

export default function ResourceUpload() {
  const { type = 'image' } = useParams<{ type: string }>()
  const [searchParams] = useSearchParams()
  const mode = searchParams.get('mode')
  const isZipMode = mode === 'zip'
  const navigate = useNavigate()

  const [items, setItems] = useState<ZipItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const zipInputRef = useRef<HTMLInputElement>(null)

  const [sources, setSources] = useState<Source[]>([])
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [sourceName, setSourceName] = useState<string>('')
  const [groups, setGroups] = useState<GroupNode[]>([])
  const [configLoaded, setConfigLoaded] = useState(false)
  const [zipError, setZipError] = useState<string>('')

  const typeNum = RESOURCE_TYPE_MAP[type]
  const typeLabel = TYPE_LABELS[type] || '文件'

  const sourceIdParam = searchParams.get('sourceId')

  const convertToTreeData = (nodes: GroupNode[]): any[] =>
    nodes.map(node => ({
      value: node.id,
      title: node.name,
      children: node.children?.length ? convertToTreeData(node.children) : []
    }))

  useEffect(() => {
    api.getSources()
      .then(data => {
        const filtered = data.items.filter(s => s.resource_type === typeNum)
        setSources(filtered)
        if (sourceIdParam) {
          const s = filtered.find(x => x.id === Number(sourceIdParam))
          if (s) {
            setSourceId(s.id)
            setSourceName(s.name)
          }
        }
      })
      .catch(() => message.error('加载来源失败'))
  }, [typeNum, sourceIdParam])

  useEffect(() => {
    if (sourceId) {
      api.getGroups(type, sourceId)
        .then(data => {
          if (data.items.length === 0) {
            return api.createGroup({
              resource_type: typeNum,
              source_id: sourceId,
              name: '默认分组',
              parent_id: null
            }).then(group => {
              setGroups([{ ...group, children: [], level: 0, real_path: '默认分组', sort_order: 0 }])
              setItems(prev => prev.map(item => ({ ...item, group_id: group.id, errors: { ...item.errors, group_id: '' } })))
            })
          }
          setGroups(data.items)
        })
        .catch(() => message.error('加载分组失败'))
    }
  }, [type, sourceId, typeNum])

  const handleBack = () => {
    items.forEach(item => {
      if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
    })
    navigate(`/${type}`)
  }

  const handleZipSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const zipFile = files[0]
    setZipError('')
    setConfigLoaded(false)

    // 校验 ZIP 包大小（前端限制 100MB）
    const MAX_ZIP_SIZE_MB = 100
    if (zipFile.size > MAX_ZIP_SIZE_MB * 1024 * 1024) {
      setZipError(`ZIP 包大小超过限制 (${MAX_ZIP_SIZE_MB}MB)，当前 ${(zipFile.size / 1024 / 1024).toFixed(1)}MB`)
      return
    }

    try {
      const zip = await JSZip.loadAsync(zipFile)
      
      const configFile = zip.file('config.json')
      if (!configFile) {
        setZipError('ZIP 包中缺少 config.json 文件')
        return
      }

      const configText = await configFile.async('string')
      const config = JSON.parse(configText)

      if (!config.meta || !config.data) {
        setZipError('config.json 格式错误，缺少 meta 或 data 字段')
        return
      }

      // 校验条目数量（前端限制 500 条）
      const MAX_UPLOAD_COUNT = 500
      if (config.data.length > MAX_UPLOAD_COUNT) {
        setZipError(`单次上传最多 ${MAX_UPLOAD_COUNT} 条，当前 ${config.data.length} 条`)
        return
      }

      const metaType = config.meta.type
      if (metaType !== type) {
        setZipError(`类型不匹配：config.json 中 type="${metaType}"，但当前页面是 "${type}"`)
        return
      }

      // 校验来源ID（当前不需要校验，使用 URL 参数传递的 sourceId）
      // const metaSourceId = config.meta.source_id
      // const source = sources.find(s => s.id === metaSourceId)
      // if (!source) {
      //   setZipError(`来源ID ${metaSourceId} 不存在`)
      //   return
      // }
      // setSourceId(metaSourceId)
      // setSourceName(source.name)

      if (!sourceId) {
        setZipError('请从资源管理页面进入上传')
        return
      }

      const parsedItems: ZipItem[] = []
      for (const item of config.data) {
        const uid = `${Date.now()}-${Math.random().toString(36).slice(2)}`
        
        let thumbnailBlob: Blob | null = null
        let thumbnailPreview = ''
        
        if (item.thumbnail_path) {
          const thumbFile = zip.file(item.thumbnail_path)
          if (thumbFile) {
            thumbnailBlob = await thumbFile.async('blob')
            thumbnailPreview = URL.createObjectURL(thumbnailBlob)
          }
        }

        let fileBlob: Blob | null = null
        if (item.file_path) {
          const resFile = zip.file(item.file_path)
          if (resFile) {
            fileBlob = await resFile.async('blob')
          }
        }

        const errors: Record<string, string> = {}
        if (!item.name?.trim()) errors.name = '名称不能为空'
        if (!item.group_id) errors.group_id = '分组不能为空'
        if (!item.width || item.width <= 0) errors.width = '宽度必须为正数'
        if (!item.height || item.height <= 0) errors.height = '高度必须为正数'
        if (!item.file_path && !item.file_url) errors.file = '文件路径或链接至少填一个'
        if (!thumbnailBlob) errors.thumbnail_path = '缩略图文件不存在或未上传'

        const metaJson = item.raw_data || {}
        const metaJsonString = JSON.stringify(metaJson, null, 2)

        parsedItems.push({
          uid,
          name: item.name || '',
          description: item.description || '',
          group_id: item.group_id || null,
          tags: item.tags || [],
          search_text: item.search_text || '',
          width: item.width || 0,
          height: item.height || 0,
          file_path: item.file_path || '',
          file_url: item.file_url || '',
          thumbnail_path: item.thumbnail_path || '',
          thumbnailPreview,
          raw_data: metaJson,
          raw_data_string: metaJsonString,
          fileBlob,
          thumbnailBlob,
          errors,
        })
      }

      setItems(parsedItems)
      setConfigLoaded(true)

    } catch (e) {
      setZipError('ZIP 解析失败：' + (e instanceof Error ? e.message : '未知错误'))
    }
  }

  const handleRemoveItem = (uid: string) => {
    const item = items.find(i => i.uid === uid)
    if (item?.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
    setItems(prev => prev.filter(i => i.uid !== uid))
  }

  const updateMetaJsonString = (uid: string, value: string) => {
    setItems(prev => prev.map(item => {
      if (item.uid !== uid) return item
      
      let metaJson: Record<string, unknown> = {}
      let metaJsonError = ''
      
      if (value.trim()) {
        try {
          const parsed = JSON.parse(value)
          if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
            metaJson = parsed
          } else {
            metaJsonError = 'JSON 必须是对象'
          }
        } catch {
          metaJsonError = 'JSON 格式错误'
        }
      }
      
      const errors: Record<string, string> = {}
      if (!item.name?.trim()) errors.name = '名称不能为空'
      if (!item.group_id) errors.group_id = '分组不能为空'
      if (!item.width || item.width <= 0) errors.width = '宽度必须为正数'
      if (!item.height || item.height <= 0) errors.height = '高度必须为正数'
      if (!item.file_path && !item.file_url) errors.file = '文件路径或链接至少填一个'
      if (!item.thumbnailBlob) errors.thumbnail_path = '请上传缩略图'
      if (metaJsonError) errors.raw_data = metaJsonError
      
      return { ...item, raw_data_string: value, raw_data: metaJson, errors }
    }))
  }

  const updateItem = (uid: string, field: keyof ZipItem, value: unknown) => {
    setItems(prev => prev.map(item => {
      if (item.uid !== uid) return item
      const updated = { ...item, [field]: value }
      
      const errors: Record<string, string> = {}
      if (!updated.name?.trim()) errors.name = '名称不能为空'
      if (!updated.group_id) errors.group_id = '分组不能为空'
      if (!updated.width || updated.width <= 0) errors.width = '宽度必须为正数'
      if (!updated.height || updated.height <= 0) errors.height = '高度必须为正数'
      if (!updated.file_path && !updated.file_url) errors.file = '文件路径或链接至少填一个'
      if (!updated.thumbnailBlob) errors.thumbnail_path = '请上传缩略图'
      
      return { ...updated, errors }
    }))
  }

  const validateAll = (): boolean => {
    let valid = true
    setItems(prev => prev.map(item => {
      const errors: Record<string, string> = {}
      if (!item.name?.trim()) { errors.name = '名称不能为空'; valid = false }
      if (!item.group_id) { errors.group_id = '分组不能为空'; valid = false }
      if (!item.width || item.width <= 0) { errors.width = '宽度必须为正数'; valid = false }
      if (!item.height || item.height <= 0) { errors.height = '高度必须为正数'; valid = false }
      if (!item.file_path && !item.file_url) { errors.file = '文件路径或链接至少填一个'; valid = false }
      if (!item.thumbnailBlob) { errors.thumbnail_path = '请上传缩略图'; valid = false }
      
      if (item.raw_data_string?.trim()) {
        try {
          const parsed = JSON.parse(item.raw_data_string)
          if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
            errors.raw_data = 'JSON 必须是对象'
            valid = false
          }
        } catch {
          errors.raw_data = 'JSON 格式错误'
          valid = false
        }
      }
      
      return { ...item, errors }
    }))
    return valid
  }

  const handleSubmit = async () => {
    if (!validateAll()) {
      message.error('请检查表单中的错误项')
      return
    }

    if (items.length === 0) {
      message.warning('没有数据可提交')
      return
    }

    if (!sourceId) {
      message.error('来源ID缺失')
      return
    }

    setUploading(true)
    setProgress(0)

    try {
      const formData = new FormData()
      
      // 辅助函数：根据扩展名获取 MIME type
      const getMimeType = (filename: string): string => {
        const ext = filename.split('.').pop()?.toLowerCase() || ''
        const mimeMap: Record<string, string> = {
          png: 'image/png',
          jpg: 'image/jpeg',
          jpeg: 'image/jpeg',
          gif: 'image/gif',
          svg: 'image/svg+xml',
          webp: 'image/webp',
          pdf: 'application/pdf',
          doc: 'application/msword',
          docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          txt: 'text/plain',
        }
        return mimeMap[ext] || 'application/octet-stream'
      }

      // 文件上传
      items.forEach((item, idx) => {
        if (item.fileBlob && item.file_path) {
          const filename = item.file_path.split('/').pop() || `file_${idx}`
          const file = new File([item.fileBlob], filename, { type: getMimeType(filename) })
          formData.append('files', file)
        } else {
          formData.append('files', new Blob([''], { type: 'application/octet-stream' }), '')
        }
      })
      
      // 缩略图上传（强制 PNG）
      items.forEach((item, idx) => {
        if (item.thumbnailBlob && item.thumbnail_path) {
          const filename = item.thumbnail_path.split('/').pop() || `thumb_${idx}.png`
          const file = new File([item.thumbnailBlob], filename, { type: 'image/png' })
          formData.append('thumbnails', file)
        } else {
          formData.append('thumbnails', new Blob([''], { type: 'image/png' }), '')
        }
      })

      formData.append('items', JSON.stringify(items.map(item => ({
        name: item.name.trim(),
        description: item.description.trim(),
        group_id: item.group_id,
        tags: item.tags,
        search_text: item.search_text.trim(),
        width: item.width,
        height: item.height,
        file_path: item.file_path || null,
        file_url: item.file_url.trim() || null,
        raw_data: item.raw_data,
      }))))
      formData.append('source_id', String(sourceId))

      setProgress(50)

      const res = await api.batchUpload(type, formData)

      setProgress(100)
      message.success(res.message)
      
      items.forEach(item => {
        if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
      })
      navigate(`/${type}`)
    } catch (e) {
      message.error('上传失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const handleAddItem = () => {
    const uid = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    setItems(prev => [...prev, {
      uid,
      name: '',
      description: '',
      group_id: null,
      tags: [],
      search_text: '',
      width: undefined as unknown as number,
      height: undefined as unknown as number,
      file_path: '',
      file_url: '',
      thumbnail_path: '',
      thumbnailPreview: '',
      raw_data: {},
      raw_data_string: '',
      fileBlob: null,
      thumbnailBlob: null,
      errors: {},
    }])
    if (!sourceId && sources.length > 0) {
      setSourceId(sources[0].id)
      setSourceName(sources[0].name)
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #e2e8f0',
      }}>
        <Button icon={<ArrowLeftOutlined />} onClick={handleBack} disabled={uploading}>
          返回
        </Button>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: '#1e293b' }}>
          {isZipMode ? 'ZIP上传' : '批量上传'}{typeLabel}
        </h2>
      </div>

      <input
        ref={zipInputRef}
        type="file"
        accept=".zip"
        style={{ display: 'none' }}
        onChange={e => handleZipSelect(e.target.files)}
      />

      {/* 来源选择 */}
      <div style={{ marginBottom: 16, padding: 12, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: '#64748b', fontSize: 12 }}>来源：</span>
        <Select
          value={sourceId}
          onChange={val => {
            const s = sources.find(x => x.id === val)
            setSourceId(val)
            setSourceName(s?.name || '')
          }}
          options={sources.map(s => ({ value: s.id, label: s.name }))}
          size="small"
          style={{ width: 200 }}
          placeholder="选择来源"
          disabled={uploading}
        />
        {!isZipMode && (
          <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleAddItem} disabled={uploading || !sourceId}>
            新增数据
          </Button>
        )}
      </div>

      {/* ZIP上传区域 */}
      {isZipMode && !configLoaded && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <Button
              icon={<FileZipOutlined />}
              onClick={() => zipInputRef.current?.click()}
              disabled={uploading}
            >
              选择ZIP包
            </Button>
            <span style={{ marginLeft: 12, color: '#64748b', fontSize: 13 }}>
              ZIP包最大100MB，单次最多500条
            </span>
          </div>
          <div style={{ fontSize: 12 }}>
            <a 
              href="/template.zip" 
              download
              style={{ color: '#3b82f6' }}
            >
              下载模板
            </a>
          </div>
          {zipError && (
            <div style={{ marginTop: 12, color: '#ef4444', fontSize: 13 }}>{zipError}</div>
          )}
        </div>
      )}

      {/* 数据列表 */}
      {items.length > 0 && (
        <div style={{
          flex: 1, overflowY: 'auto',
          border: '1px solid #e2e8f0', borderRadius: 8, marginBottom: 12,
        }}>
          {/* 表头 */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 12px',
            background: '#f8fafc',
            fontWeight: 500, fontSize: 11, color: '#64748b',
          }}>
            <div style={{ width: 44, flexShrink: 0 }}>缩略图</div>
            <div style={{ flex: 1, minWidth: 80 }}>名称 *</div>
            <div style={{ flex: 1, minWidth: 80 }}>描述</div>
            <div style={{ width: 100, flexShrink: 0 }}>分组 *</div>
            <div style={{ width: 50, flexShrink: 0 }}>宽 *</div>
            <div style={{ width: 50, flexShrink: 0 }}>高 *</div>
            <div style={{ flex: 1, minWidth: 80 }}>文件路径</div>
            <div style={{ flex: 1, minWidth: 100 }}>文件链接</div>
            <div style={{ flex: 1, minWidth: 80 }}>标签</div>
            <div style={{ flex: 1, minWidth: 80 }}>搜索词</div>
            <div style={{ flex: 1, minWidth: 100 }}>元数据</div>
            <div style={{ width: 28, flexShrink: 0 }}></div>
          </div>
          {/* 数据行 */}
          {items.map(item => (
            <div
              key={item.uid}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px',
                borderBottom: '1px solid #f1f5f9',
              }}
            >
              <div style={{ width: 44, flexShrink: 0 }}>
                {item.thumbnailPreview ? (
                  <div style={{ position: 'relative' }}>
                    <Image
                      src={item.thumbnailPreview}
                      width={36}
                      height={36}
                      style={{ borderRadius: 4, objectFit: 'cover' }}
                    />
                    <input
                      type="file"
                      accept="image/png"
                      style={{ position: 'absolute', top: 0, left: 0, width: 36, height: 36, opacity: 0, cursor: 'pointer' }}
                      onChange={e => {
                        const file = e.target.files?.[0]
                        if (file && file.type === 'image/png') {
                          const preview = URL.createObjectURL(file)
                          if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
                          setItems(prev => prev.map(i => i.uid === item.uid ? { ...i, thumbnailBlob: file, thumbnailPreview: preview, thumbnail_path: file.name, errors: { ...i.errors, thumbnail_path: '' } } : i))
                        } else if (file) {
                          message.error('缩略图仅支持 PNG 格式')
                        }
                      }}
                      disabled={uploading}
                    />
                  </div>
                ) : (
                  <div style={{ position: 'relative' }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 4, background: '#f1f5f9',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 11, cursor: 'pointer',
                      border: item.errors.thumbnail_path ? '1px solid #ef4444' : '1px dashed #cbd5e1',
                    }}>
                      <UploadOutlined />
                    </div>
                    <input
                      type="file"
                      accept="image/png"
                      style={{ position: 'absolute', top: 0, left: 0, width: 36, height: 36, opacity: 0, cursor: 'pointer' }}
                      onChange={e => {
                        const file = e.target.files?.[0]
                        if (file && file.type === 'image/png') {
                          const preview = URL.createObjectURL(file)
                          setItems(prev => prev.map(i => i.uid === item.uid ? { ...i, thumbnailBlob: file, thumbnailPreview: preview, thumbnail_path: file.name, errors: { ...i.errors, thumbnail_path: '' } } : i))
                        } else if (file) {
                          message.error('缩略图仅支持 PNG 格式')
                        }
                      }}
                      disabled={uploading}
                    />
                  </div>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 80 }}>
                <Input
                  value={item.name}
                  onChange={e => updateItem(item.uid, 'name', e.target.value)}
                  size="small"
                  status={item.errors.name ? 'error' : undefined}
                  disabled={uploading}
                />
              </div>
              <div style={{ flex: 1, minWidth: 80 }}>
                <Input
                  value={item.description}
                  onChange={e => updateItem(item.uid, 'description', e.target.value)}
                  size="small"
                  disabled={uploading}
                />
              </div>
              <div style={{ width: 100, flexShrink: 0 }}>
                <TreeSelect
                  value={item.group_id}
                  onChange={val => updateItem(item.uid, 'group_id', val)}
                  treeData={convertToTreeData(groups)}
                  size="small"
                  style={{ width: '100%' }}
                  placeholder="选择分组"
                  status={item.errors.group_id ? 'error' : undefined}
                  disabled={uploading}
                />
              </div>
              <div style={{ width: 50, flexShrink: 0 }}>
                <InputNumber
                  value={item.width}
                  onChange={val => updateItem(item.uid, 'width', val)}
                  size="small"
                  min={0}
                  style={{ width: '100%' }}
                  status={item.errors.width ? 'error' : undefined}
                  disabled={uploading}
                />
              </div>
              <div style={{ width: 50, flexShrink: 0 }}>
                <InputNumber
                  value={item.height}
                  onChange={val => updateItem(item.uid, 'height', val)}
                  size="small"
                  min={0}
                  style={{ width: '100%' }}
                  status={item.errors.height ? 'error' : undefined}
                  disabled={uploading}
                />
              </div>
              <div style={{ flex: 1, minWidth: 80 }}>
                <div style={{ position: 'relative' }}>
                  <Tooltip title={item.file_path || '点击上传文件'}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      padding: '4px 8px', background: '#f8fafc', borderRadius: 4, cursor: 'pointer',
                      fontSize: 11, color: item.file_path ? '#1e293b' : '#94a3b8',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      border: item.errors.file ? '1px solid #ef4444' : 'none',
                    }}>
                      {item.fileBlob ? (
                        <UploadOutlined style={{ fontSize: 10 }} />
                      ) : null}
                      {item.file_path || '上传文件'}
                    </div>
                  </Tooltip>
                  <input
                    type="file"
                    accept={type === 'image' ? 'image/png,image/svg+xml,image/jpeg,image/webp' : undefined}
                    style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
                    onChange={e => {
                      const file = e.target.files?.[0]
                      if (file) {
                        const isPng = file.type === 'image/png'
                        const isImageType = type === 'image'
                        setItems(prev => prev.map(i => {
                          if (i.uid !== item.uid) return i
                          const updates: Partial<ZipItem> = { 
                            fileBlob: file, 
                            file_path: file.name, 
                            errors: { ...i.errors, file: '' } 
                          }
                          if (isImageType && isPng) {
                            updates.thumbnailBlob = file
                            updates.thumbnailPreview = URL.createObjectURL(file)
                            updates.thumbnail_path = file.name
                            if (updates.errors) updates.errors.thumbnail_path = ''
                          }
                          return { ...i, ...updates }
                        }))
                      }
                    }}
                    disabled={uploading}
                  />
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 100 }}>
                <Input
                  value={item.file_url}
                  onChange={e => {
                    const val = e.target.value
                    setItems(prev => prev.map(i => {
                      if (i.uid !== item.uid) return i
                      const errors = { ...i.errors }
                      if (val.trim() || i.file_path) errors.file = ''
                      return { ...i, file_url: val, errors }
                    }))
                  }}
                  size="small"
                  placeholder="https://"
                  status={item.errors.file ? 'error' : undefined}
                  disabled={uploading}
                />
                {item.errors.file && (
                  <div style={{ color: '#ef4444', fontSize: 10, marginTop: 2 }}>{item.errors.file}</div>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 80 }}>
                <Select
                  mode="tags"
                  value={item.tags}
                  onChange={val => updateItem(item.uid, 'tags', val)}
                  size="small"
                  style={{ width: '100%' }}
                  tokenSeparators={[',']}
                  disabled={uploading}
                />
              </div>
              <div style={{ flex: 1, minWidth: 80 }}>
                <Input
                  value={item.search_text}
                  onChange={e => updateItem(item.uid, 'search_text', e.target.value)}
                  size="small"
                  placeholder="关键词"
                  disabled={uploading}
                />
              </div>
              <div style={{ flex: 1, minWidth: 100 }}>
                <Input.TextArea
                  value={item.raw_data_string}
                  onChange={e => updateMetaJsonString(item.uid, e.target.value)}
                  size="small"
                  placeholder="{}"
                  autoSize={{ minRows: 1, maxRows: 3 }}
                  status={item.errors.raw_data ? 'error' : undefined}
                  disabled={uploading}
                />
                {item.errors.raw_data && (
                  <div style={{ color: '#ef4444', fontSize: 10, marginTop: 2 }}>{item.errors.raw_data}</div>
                )}
              </div>
              <div style={{ width: 28, flexShrink: 0 }}>
                <Button
                  type="text"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={() => handleRemoveItem(item.uid)}
                  disabled={uploading}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {uploading && (
        <Progress
          percent={progress}
          status="active"
          format={() => `上传进度：${progress}%`}
          style={{ marginBottom: 12 }}
        />
      )}

      {items.length > 0 && sourceId && (
        <div style={{
          display: 'flex', justifyContent: 'flex-end', gap: 8,
          paddingTop: 16, borderTop: '1px solid #f1f5f9',
        }}>
          <Button onClick={handleBack} disabled={uploading}>取消</Button>
          <Button
            type="primary"
            onClick={handleSubmit}
            loading={uploading}
            disabled={items.length === 0}
          >
            {uploading ? '上传中...' : `提交 ${items.length} 个`}
          </Button>
        </div>
      )}
    </div>
  )
}