import { useState, useEffect, useRef } from 'react'
import { Button, message } from 'antd'
import { api } from '../api'

/**
 * 详情抽屉预览图下方的「图片语义生成」按钮 + 结果展示。
 * 调用 POST /api/resources/{id}/understand，对资源预览图生成中文语义描述。
 */
export default function SemanticUnderstand({ resourceId, onFill }: {
  resourceId: number
  onFill: (text: string) => void
}) {
  const [loading, setLoading] = useState(false)
  const [text, setText] = useState<string | null>(null)
  const idRef = useRef(resourceId)

  useEffect(() => {
    idRef.current = resourceId
    setText(null)
    setLoading(false)
  }, [resourceId])

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const res = await api.understandImage(resourceId)
      if (idRef.current === resourceId) setText(res.description)
    } catch (e: unknown) {
      message.error('语义生成失败：' + (e instanceof Error ? e.message : '未知错误'))
    } finally {
      if (idRef.current === resourceId) setLoading(false)
    }
  }

  return (
    <div style={{ marginTop: 12 }}>
      <Button block loading={loading} onClick={handleGenerate}>
        {loading ? '生成中，预计需 10~30 秒' : '图片语义生成'}
      </Button>
      {text && (
        <div style={{
          marginTop: 10, padding: '10px 12px', background: '#f8fafc',
          border: '1px solid #e2e8f0', borderRadius: 8,
          fontSize: 13, color: '#334155', lineHeight: 1.6,
        }}>
          {text}
          <div style={{ marginTop: 8, textAlign: 'right' }}>
            <Button
              size="small"
              type="link"
              style={{ padding: 0, height: 'auto' }}
              onClick={() => onFill(text)}
            >
              追加到描述
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
