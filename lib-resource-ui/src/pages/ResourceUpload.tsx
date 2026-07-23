import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button, Input, Select, message, Progress, Image, Tooltip, Upload, Spin } from 'antd'
import { ArrowLeftOutlined, DeleteOutlined, FileZipOutlined, PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons'
import JSZip from 'jszip'
import { api, Source, GroupNode } from '../api'

interface ZipItem {
  uid: string
  name: string
  file_name: string
  description: string
  group_id: number | null
  tags: string[]
  search_text: string
  width: number | null
  height: number | null
  file_path: string
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

const MAX_UPLOAD_COUNT = 50000

const findGroupById = (nodes: GroupNode[], targetId: number): GroupNode | null => {
  for (const node of nodes) {
    if (node.id === targetId) return node
    if (node.children) {
      const found = findGroupById(node.children, targetId)
      if (found) return found
    }
  }
  return null
}

const getImageDimensions = (file: Blob): Promise<{ width: number; height: number }> => {
  return new Promise((resolve, reject) => {
    const img = new window.Image()
    img.onload = () => {
      resolve({ width: img.width, height: img.height })
      URL.revokeObjectURL(img.src)
    }
    img.onerror = () => {
      URL.revokeObjectURL(img.src)
      reject(new Error('Failed to load image'))
    }
    img.src = URL.createObjectURL(file)
  })
}

const withTimeout = <T extends unknown>(promise: Promise<T>, timeoutMs: number, errorMsg: string): Promise<T> => {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(errorMsg)), timeoutMs)
    )
  ])
}

export default function ResourceUpload() {
  const { type = 'image' } = useParams<{ type: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [items, setItems] = useState<ZipItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const zipInputRef = useRef<HTMLInputElement>(null)
  const [zipLoading, setZipLoading] = useState(false)
  const [zipProgress, setZipProgress] = useState('')

  const [sources, setSources] = useState<Source[]>([])
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [sourceName, setSourceName] = useState<string>('')
  const [groupId, setGroupId] = useState<number | null>(null)
  const [groupName, setGroupName] = useState<string>('')
  const [configLoaded, setConfigLoaded] = useState(false)
  const [zipError, setZipError] = useState<string>('')
  const [pageLoading, setPageLoading] = useState(true)
  const validatedRef = useRef(false)

  const typeNum = RESOURCE_TYPE_MAP[type]
  const typeLabel = TYPE_LABELS[type] || '文件'

  const sourceIdParam = searchParams.get('sourceId')
  const groupIdParam = searchParams.get('groupId')

  const navigateToManage = useCallback(() => {
    const params = new URLSearchParams()
    if (sourceIdParam) params.set('sourceId', sourceIdParam)
    if (groupIdParam) params.set('groupId', groupIdParam)
    navigate(params.toString() ? `/${type}?${params.toString()}` : `/${type}`)
  }, [sourceIdParam, groupIdParam, type, navigate])

  useEffect(() => {
    // 防止 StrictMode 双重执行
    if (validatedRef.current) return
    validatedRef.current = true
    
    const validateAndLoad = async () => {
      // 提前验证 URL 参数
      if (!sourceIdParam) {
        message.error('请从资源管理页面进入')
        navigateToManage()
        return
      }
      
      const sourceIdNum = Number(sourceIdParam)
      if (isNaN(sourceIdNum)) {
        message.error('来源ID格式错误')
        navigateToManage()
        return
      }
      
      setPageLoading(true)
      
      try {
        const [sourcesData, groupsData] = await Promise.all([
          api.getSources(),
          api.getGroups(type, sourceIdNum, false)
        ])
        
        const filtered = sourcesData.items.filter(s => s.resource_type === typeNum)
        setSources(filtered)
        
        const source = filtered.find(x => x.id === sourceIdNum)
        if (!source) {
          message.error('来源不存在')
          navigateToManage()
          return
        }
        setSourceId(source.id)
        setSourceName(source.name)
        
        if (groupsData.items.length === 0) {
          message.error('请先创建分组')
          navigateToManage()
          return
        }
        
        if (groupIdParam) {
          const groupIdNum = Number(groupIdParam)
          if (isNaN(groupIdNum)) {
            message.error('分组ID格式错误')
            navigateToManage()
            return
          }
          
          const group = findGroupById(groupsData.items, groupIdNum)
          if (!group) {
            message.error('分组不存在')
            navigateToManage()
            return
          }

          setGroupId(group.id)
          setGroupName(group.name)
        } else {
          const firstGroup = groupsData.items[0]
          if (firstGroup) {
            setGroupId(firstGroup.id)
            setGroupName(firstGroup.name)
          } else {
            message.error('请先创建或选中分组')
            navigateToManage()
            return
          }
        }
        
        setConfigLoaded(true)
      } catch (e) {
        message.error('加载数据失败')
        console.error('加载失败:', e)
      } finally {
        setPageLoading(false)
      }
    }
    
    validateAndLoad()
  }, [sourceIdParam, groupIdParam, type, typeNum, navigateToManage])

  const handleBack = () => {
    items.forEach(item => {
      if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
    })
    navigateToManage()
  }

  const handleZipSelect = async (files: FileList | null) => {
    console.log('=== handleZipSelect called ===')
    console.log('files:', files)
    
    if (!files || files.length === 0) {
      console.log('No files selected')
      return
    }
    
    const zipFile = files[0]
    console.log('ZIP file:', {
      name: zipFile.name,
      size: zipFile.size,
      type: zipFile.type
    })
    
    console.log('Initial state:', {
      configLoaded,
      zipLoading,
      zipError,
      sourceId,
      sourceIdParam,
      groupIdParam
    })
    
    setZipError('')
    setConfigLoaded(false)

    console.log('File size check passed, starting to load ZIP')
    
    setZipLoading(true)
    setZipProgress('正在加载 ZIP 文件...')
    console.log('State updated: zipLoading=true, zipProgress set')

    try {
      console.log('Calling JSZip.loadAsync...')
      // 加载 ZIP（已移除超时限制，支持大文件）
      const zip = await JSZip.loadAsync(zipFile)
      console.log('ZIP loaded successfully')

      setZipProgress('正在解析配置文件...')
      console.log('Parsing config.json...')

      const configFile = zip.file('config.json')
      console.log('Config file found:', !!configFile)
      
      if (!configFile) {
        setZipError('ZIP 包中缺少 config.json 文件')
        console.log('ERROR: config.json not found')
        return
      }

      // 读取 config.json（已移除超时限制）
      console.log('Reading config.json content...')
      const configText = await configFile.async('string')
      console.log('Config text length:', configText.length)

      const config = JSON.parse(configText)
      console.log('Config parsed:', {
        meta: config.meta,
        dataLength: config.data?.length
      })

      console.log('=== Starting validations ===')
      console.log('config.meta:', config.meta)
      console.log('config.data.length:', config.data.length)
      console.log('type from URL:', type)
      console.log('sourceIdParam:', sourceIdParam)
      console.log('groupIdParam:', groupIdParam)
      console.log('sourceId state:', sourceId)
      
      if (!config.meta || !config.data) {
        setZipError('config.json 格式错误，缺少 meta 或 data 字段')
        console.log('❌ ERROR: Missing meta or data')
        return
      }
      console.log('✓ meta and data exist')

      // 校验条目数量
      if (config.data.length > MAX_UPLOAD_COUNT) {
        setZipError(`单次上传最多 ${MAX_UPLOAD_COUNT} 条，当前 ${config.data.length} 条`)
        console.log('❌ ERROR: Too many items')
        return
      }
      console.log(`✓ Items count OK: ${config.data.length}`)

      const metaType = config.meta.type
      console.log('Type check:', { metaType, currentType: type })
      if (metaType !== type) {
        console.log('=== Validation failed ===')
        console.log('Setting zipError:', `类型不匹配：config.json 中 type="${metaType}"，但当前页面是 "${type}"`)
        console.log('Current zipError before set:', zipError)
        setZipError(`类型不匹配：config.json 中 type="${metaType}"，但当前页面是 "${type}"`)
        console.log('zipError set, returning from try block')
        return
      }
      console.log('✓ Type matches')

      // 验证来源ID一致性
      const metaSourceId = config.meta.source_id
      console.log('Source ID check:', { 
        metaSourceId, 
        sourceIdParam, 
        sourceIdParamNumber: Number(sourceIdParam),
        isEqual: metaSourceId === Number(sourceIdParam)
      })
      if (metaSourceId !== Number(sourceIdParam)) {
        setZipError(`来源ID不一致：config.json 中 source_id=${metaSourceId}，当前页面 sourceId=${sourceIdParam}`)
        console.log('❌ ERROR: Source ID mismatch')
        return
      }
      console.log('✓ Source ID matches')

      // 验证分组ID一致性（如果有）
      const metaGroupId = config.meta.group_id
      console.log('Group ID check:', { 
        metaGroupId, 
        groupIdParam, 
        groupIdParamNumber: Number(groupIdParam),
        shouldCheck: metaGroupId && groupIdParam,
        isEqual: metaGroupId === Number(groupIdParam)
      })
      if (metaGroupId && groupIdParam && metaGroupId !== Number(groupIdParam)) {
        setZipError(`分组ID不一致：config.json 中 group_id=${metaGroupId}，当前页面 groupId=${groupIdParam}`)
        console.log('❌ ERROR: Group ID mismatch')
        return
      }
      console.log('✓ Group ID matches')

      console.log('sourceId state check:', sourceId)
      if (!sourceId) {
        setZipError('请从资源管理页面进入上传')
        console.log('❌ ERROR: sourceId is null')
        return
      }
      console.log('✓ sourceId state OK')

      console.log('All validations passed, starting to parse items...')
      
      const parsedItems: ZipItem[] = []
      const totalItems = config.data.length
      console.log(`Total items to parse: ${totalItems}`)

      for (let idx = 0; idx < config.data.length; idx++) {
        const item = config.data[idx]
        if (idx % 10 === 0) {
          console.log(`Parsing item ${idx + 1}/${totalItems}`)
        }
        setZipProgress(`正在解析第 ${idx + 1}/${totalItems} 个资源...`)

        const uid = `${Date.now()}-${Math.random().toString(36).slice(2)}`

        let thumbnailBlob: Blob | null = null
        let thumbnailPreview = ''
        let width: number | null = null
        let height: number | null = null

        if (item.thumbnail_path) {
          const thumbFile = zip.file(item.thumbnail_path)
          if (thumbFile) {
            thumbnailBlob = await thumbFile.async('blob')
            thumbnailPreview = URL.createObjectURL(thumbnailBlob)

            // 从缩略图读取宽高
            try {
              const dims = await getImageDimensions(thumbnailBlob)
              width = dims.width
              height = dims.height
            } catch {
              // 忽略错误，宽高保持 null
            }
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
        // 缩略图可选，不强制验证

        const rawData = item.raw_data || {}
        const rawDataString = JSON.stringify(rawData, null, 2)

        const fileName = item.file_name || (item.file_path ? item.file_path.split('/').pop()?.replace(/\.[^/.]+$/, '') : '')

        parsedItems.push({
          uid,
          name: item.name || '',
          file_name: fileName,
          description: item.description || '',
          group_id: groupId,
          tags: item.tags || [],
          search_text: item.search_text || '',
          width,
          height,
          file_path: item.file_path || '',
          thumbnail_path: item.thumbnail_path || '',
          thumbnailPreview,
          raw_data: rawData,
          raw_data_string: rawDataString,
          fileBlob,
          thumbnailBlob,
          errors,
        })
      }

      setZipProgress('解析完成')
      console.log('All items parsed, total:', parsedItems.length)
      
      setItems(parsedItems)
      setConfigLoaded(true)
      console.log('State updated: items set, configLoaded=true')

    } catch (e) {
      console.error('Error in handleZipSelect:', e)
      if (e instanceof Error) {
        setZipError(e.message)
        console.log('Error message:', e.message)
      } else {
        setZipError('ZIP 解析失败：' + String(e))
        console.log('Unknown error:', String(e))
      }
    } finally {
      console.log('=== Finally block ===')
      console.log('Before setState:', {
        zipLoading,
        zipError,
        configLoaded
      })
      setZipLoading(false)
      setZipProgress('')
      console.log('After setState (will trigger re-render)')
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
      
      return { ...updated, errors }
    }))
  }

  const validateAll = (): boolean => {
    let valid = true
    setItems(prev => prev.map(item => {
      const errors: Record<string, string> = {}
      if (!item.name?.trim()) { errors.name = '名称不能为空'; valid = false }
      
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
      
      // 缩略图上传
      items.forEach((item, idx) => {
        if (item.thumbnailBlob && item.thumbnail_path) {
          const filename = item.thumbnail_path.split('/').pop() || `thumb_${idx}.png`
          const file = new File([item.thumbnailBlob], filename, { type: getMimeType(filename) })
          formData.append('thumbnails', file)
        } else {
          formData.append('thumbnails', new Blob([''], { type: 'application/octet-stream' }), '')
        }
      })

      formData.append('items', JSON.stringify(items.map(item => ({
        name: item.name.trim(),
        file_name: item.file_name?.trim() || null,
        description: item.description.trim(),
        group_id: item.group_id,
        tags: item.tags,
        search_text: item.search_text.trim(),
        width: item.width,
        height: item.height,
        file_path: item.file_path || null,
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
      navigateToManage()
    } catch (e) {
      message.error('上传失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const handleAddItem = () => {
    if (items.length >= MAX_UPLOAD_COUNT) {
      message.warning(`最多添加 ${MAX_UPLOAD_COUNT} 条数据`)
      return
    }
    const uid = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    setItems(prev => [...prev, {
      uid,
      name: '',
      file_name: '',
      description: '',
      group_id: groupId,
      tags: [],
      search_text: '',
      width: null,
      height: null,
      file_path: '',
      thumbnail_path: '',
      thumbnailPreview: '',
      raw_data: {},
      raw_data_string: '',
      fileBlob: null,
      thumbnailBlob: null,
      errors: {},
    }])
  }

  const downloadTemplate = async () => {
    const zip = new JSZip()
    
    const config = {
      meta: {
        type: type,
        source_id: sourceId,
        group_id: groupId
      },
      data: [
        {
          name: "示例资源",
          file_name: "example.svg",
          file_path: "data/example.svg",
          thumbnail_path: "image/example.png",
          description: "示例描述",
          tags: ["示例"],
          search_text: "关键词",
          raw_data: {}
        }
      ]
    }
    
    zip.file("config.json", JSON.stringify(config, null, 2))
    
    // 创建 README.md
    const readme = `# ZIP 上传模板说明

## 文件结构
\`\`\`
├── config.json      # 配置文件（必填）
├── image/           # 缩略图目录
│   └── example.png
└── data/            # 资源文件目录
    └── example.svg
\`\`\`

## config.json 字段说明

### meta 字段（元信息）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 资源类型：component/icon/illus/template/image/file |
| source_id | number | 是 | 来源ID（已自动填充，请勿修改） |
| group_id | number | 否 | 分组ID（已自动填充，请勿修改） |

### data 字段（资源列表）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 资源名称 |
| file_name | string | 否 | 展示文件名（用于前端显示） |
| file_path | string | 否 | 文件在ZIP中的相对路径 |
| thumbnail_path | string | 否 | 缩略图在ZIP中的相对路径（支持 PNG/SVG/JPEG 格式，宽高自动读取），可选 |
| description | string | 否 | 资源描述 |
| tags | array | 否 | 标签数组 |
| search_text | string | 否 | 搜索关键词 |
| raw_data | object | 否 | 自定义元数据 |

## 注意事项
1. meta.source_id 和 meta.group_id 已根据当前页面自动填充，请勿修改
2. 缩略图支持 PNG/SVG/JPEG 格式，宽高会自动读取
3. file_path 可选，如果不上传文件可以留空
`
    zip.file("README.md", readme)
    
    // 创建最小的示例 PNG 文件（1x1 像素）
    const minPNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    const pngBlob = await fetch(minPNG).then(r => r.blob())
    zip.file("image/example.png", pngBlob)
    
    // 创建最小的示例 SVG 文件
    const minSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><rect width="24" height="24" fill="#ccc"/></svg>'
    zip.file("data/example.svg", minSVG)
    
    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${type}_template.zip`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (pageLoading && !configLoaded) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #e2e8f0',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={handleBack} disabled={uploading}>
            返回
          </Button>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: '#1e293b' }}>
            批量上传{typeLabel}
          </h2>
          <span style={{ color: '#64748b', fontSize: 14 }}>
            来源：{sourceName} | 分组：{groupName}
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: 8 }}>
          <Button onClick={handleAddItem} disabled={uploading || !sourceId || items.length >= MAX_UPLOAD_COUNT}>
            新增数据
          </Button>
          <Button
            icon={<FileZipOutlined />}
            onClick={() => zipInputRef.current?.click()}
            disabled={uploading || zipLoading}
          >
            ZIP上传
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={downloadTemplate}
            disabled={uploading}
          >
            下载模板
          </Button>
          <Button onClick={handleBack} disabled={uploading}>
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

      <input
        ref={zipInputRef}
        type="file"
        accept=".zip"
        style={{ display: 'none' }}
        onChange={e => handleZipSelect(e.target.files)}
      />

      {/* 进度提示 */}
      {zipLoading && (
        <div style={{
          marginBottom: 16,
          padding: 12,
          background: '#eff6ff',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{ color: '#1e40af', fontSize: 14 }}>
            {zipProgress || '正在解析 ZIP 文件...'}
          </span>
        </div>
      )}

      {/* 错误提示 */}
      {zipError && (
        <div style={{
          marginBottom: 16,
          padding: 12,
          background: '#fef2f2',
          borderRadius: 6,
          color: '#ef4444',
          fontSize: 13,
          whiteSpace: 'pre-wrap',
        }}>
          {zipError}
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
            <div style={{ flex: 1, minWidth: 80 }}>标签</div>
            <div style={{ flex: 1, minWidth: 80 }}>关键词</div>
            <div style={{ flex: 1, minWidth: 100 }}>元数据</div>
            <div style={{ flex: 1, minWidth: 80 }}>文件</div>
            <div style={{ flex: 1, minWidth: 80 }}>文件名</div>
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
                      fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzYiIGhlaWdodD0iMzYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjM2IiBoZWlnaHQ9IjM2IiBmaWxsPSIjZjFmNWY5Ii8+PHRleHQgeD0iMTgiIHk9IjE4IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iOCIgZmlsbD0iIzk0YTNiOCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuengeWKoOiKseeDn+iKseeBhjwvdGV4dD48L3N2Zz4="
                    />
                    <input
                      type="file"
                      accept="image/png,image/svg+xml,image/jpeg"
                      style={{ position: 'absolute', top: 0, left: 0, width: 36, height: 36, opacity: 0, cursor: 'pointer' }}
                      onChange={e => {
                        const file = e.target.files?.[0]
                        if (file) {
                          const preview = URL.createObjectURL(file)
                          if (item.thumbnailPreview) URL.revokeObjectURL(item.thumbnailPreview)
                          
                          getImageDimensions(file)
                            .then(({ width, height }) => {
                              setItems(prev => prev.map(i => i.uid === item.uid ? { 
                                ...i, 
                                thumbnailBlob: file, 
                                thumbnailPreview: preview, 
                                thumbnail_path: file.name,
                                width,
                                height,
                                errors: { ...i.errors, thumbnail_path: '' } 
                              } : i))
                            })
                            .catch(() => {
                              setItems(prev => prev.map(i => i.uid === item.uid ? { 
                                ...i, 
                                thumbnailBlob: file, 
                                thumbnailPreview: preview, 
                                thumbnail_path: file.name,
                                errors: { ...i.errors, thumbnail_path: '' } 
                              } : i))
                            })
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
                      accept="image/png,image/svg+xml,image/jpeg"
                      style={{ position: 'absolute', top: 0, left: 0, width: 36, height: 36, opacity: 0, cursor: 'pointer' }}
                      onChange={e => {
                        const file = e.target.files?.[0]
                        if (file) {
                          const preview = URL.createObjectURL(file)
                          
                          getImageDimensions(file)
                            .then(({ width, height }) => {
                              setItems(prev => prev.map(i => i.uid === item.uid ? { 
                                ...i, 
                                thumbnailBlob: file, 
                                thumbnailPreview: preview, 
                                thumbnail_path: file.name,
                                width,
                                height,
                                errors: { ...i.errors, thumbnail_path: '' } 
                              } : i))
                            })
                            .catch(() => {
                              setItems(prev => prev.map(i => i.uid === item.uid ? { 
                                ...i, 
                                thumbnailBlob: file, 
                                thumbnailPreview: preview, 
                                thumbnail_path: file.name,
                                errors: { ...i.errors, thumbnail_path: '' } 
                              } : i))
                            })
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
                <Input.TextArea
                  value={item.search_text}
                  onChange={e => updateItem(item.uid, 'search_text', e.target.value)}
                  size="small"
                  placeholder="关键词"
                  autoSize={{ minRows: 1, maxRows: 3 }}
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
              <div style={{ flex: 1, minWidth: 80 }}>
                <div style={{ position: 'relative' }}>
                  <Tooltip title={item.file_path || '点击上传文件'}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      padding: '4px 8px', background: '#f8fafc', borderRadius: 4, cursor: 'pointer',
                      fontSize: 11, color: item.file_path ? '#1e293b' : '#94a3b8',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
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
                         const fileName = file.name.replace(/\.[^/.]+$/, "")
                         setItems(prev => prev.map(i => {
                           if (i.uid !== item.uid) return i
                           const updates: Partial<ZipItem> = { 
                             fileBlob: file, 
                             file_path: file.name,
                             file_name: i.file_name || fileName,
                           }
                           if (isImageType && isPng) {
                             updates.thumbnailBlob = file
                             updates.thumbnailPreview = URL.createObjectURL(file)
                             updates.thumbnail_path = file.name
                           }
                           return { ...i, ...updates }
                         }))
                       }
                     }}
                    disabled={uploading}
                  />
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 80 }}>
                <Input
                  value={item.file_name}
                  onChange={e => updateItem(item.uid, 'file_name', e.target.value)}
                  size="small"
                  placeholder="展示文件名"
                  disabled={uploading}
                />
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
    </div>
  )
}