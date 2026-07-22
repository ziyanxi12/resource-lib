import { useState, useEffect, useRef } from 'react'
import { Button, message } from 'antd'
import { api } from '../api'

/**
 * 图片语义生成按钮组件。
 * 调用 POST /api/resources/{id}/understand，对资源预览图生成中文语义描述。
 */
export default function SemanticUnderstand({ resourceId, prompt, onGenerated }: {
  resourceId: number
  prompt?: string
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
      const res = await api.understandImage(resourceId, prompt)
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
