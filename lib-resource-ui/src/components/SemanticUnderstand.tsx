import { useState, useEffect, useRef } from 'react'
import { Button, message } from 'antd'
import { api } from '../api'

const SVG_MAX_EDGE = 1024

function isSvgExt(name?: string): boolean {
  return !!name && /\.svg(\?|$)/i.test(name)
}

function stripDataUrl(dataUrl: string): string {
  const idx = dataUrl.indexOf(',')
  return idx >= 0 ? dataUrl.slice(idx + 1) : dataUrl
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error ?? new Error('读取文件失败'))
    reader.readAsDataURL(file)
  })
}

function svgToPngDataUrl(src: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      let w = img.naturalWidth || img.width
      let h = img.naturalHeight || img.height
      if (!w || !h) {
        reject(new Error('SVG 尺寸读取失败'))
        return
      }
      const longest = Math.max(w, h)
      if (longest > SVG_MAX_EDGE) {
        const scale = SVG_MAX_EDGE / longest
        w = Math.round(w * scale)
        h = Math.round(h * scale)
      }
      const canvas = document.createElement('canvas')
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('canvas 2D 上下文不可用'))
        return
      }
      ctx.drawImage(img, 0, 0, w, h)
      try {
        resolve(canvas.toDataURL('image/png'))
      } catch (e) {
        reject(e instanceof Error ? e : new Error('canvas 导出失败'))
      }
    }
    img.onerror = () => reject(new Error('SVG 加载失败'))
    img.src = src
  })
}

async function urlToDataUrl(url: string): Promise<string> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`获取图片失败: HTTP ${res.status}`)
  const blob = await res.blob()
  if (isSvgExt(url) || blob.type === 'image/svg+xml') {
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(reader.error ?? new Error('读取 SVG 失败'))
      reader.readAsDataURL(blob)
    })
    return svgToPngDataUrl(dataUrl)
  }
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error ?? new Error('读取图片失败'))
    reader.readAsDataURL(blob)
  })
}

async function imageToBase64(source: { url?: string; file?: File }): Promise<string> {
  if (source.file) {
    const file = source.file
    if (file.type === 'image/svg+xml' || isSvgExt(file.name)) {
      const objUrl = URL.createObjectURL(file)
      try {
        const dataUrl = await svgToPngDataUrl(objUrl)
        return stripDataUrl(dataUrl)
      } finally {
        URL.revokeObjectURL(objUrl)
      }
    }
    const dataUrl = await fileToDataUrl(file)
    return stripDataUrl(dataUrl)
  }
  if (source.url) {
    const dataUrl = await urlToDataUrl(source.url)
    return stripDataUrl(dataUrl)
  }
  throw new Error('缺少预览图')
}

export interface ThumbnailSource {
  url?: string
  file?: File
}

/**
 * 图片语义生成按钮组件。
 * 调用 POST /api/resources/{id}/understand，对资源预览图生成中文语义描述。
 * 预览图由前端构造为 base64（PNG/JPEG 直传，SVG 经 canvas 转 PNG）后随请求发送。
 */
export default function SemanticUnderstand({ resourceId, prompt, thumbnail, onGenerated }: {
  resourceId: number
  prompt?: string
  thumbnail?: ThumbnailSource
  onGenerated?: (text: string, elapsed: number) => void
}) {
  const [loading, setLoading] = useState(false)
  const idRef = useRef(resourceId)

  useEffect(() => {
    idRef.current = resourceId
    setLoading(false)
  }, [resourceId])

  const handleGenerate = async () => {
    setLoading(true)
    const start = Date.now()
    try {
      let imageBase64: string | undefined
      if (thumbnail && (thumbnail.url || thumbnail.file)) {
        imageBase64 = await imageToBase64(thumbnail)
      }
      const res = await api.understandImage(resourceId, { prompt, imageBase64 })
      const elapsed = Math.floor((Date.now() - start) / 1000)
      if (idRef.current === resourceId) {
        onGenerated?.(res.description, elapsed)
      }
    } catch (e: unknown) {
      message.error('语义生成失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      if (idRef.current === resourceId) setLoading(false)
    }
  }

  return (
    <Button block loading={loading} onClick={handleGenerate} style={{ marginTop: 12 }}>
      {loading ? '生成中...' : '图片语义生成'}
    </Button>
  )
}
