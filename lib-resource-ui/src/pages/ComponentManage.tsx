import { useState, useEffect } from 'react'
import { Button, Alert, Spin, Space, Statistic, Typography, message, Tag } from 'antd'
import { SyncOutlined, BlockOutlined, CheckCircleFilled } from '@ant-design/icons'
import { api } from '../api'
import type { ComponentMapItem, SyncResult } from '../types'

interface SyncState {
  loading: boolean
  result?: SyncResult
  error?: string
}

export default function ComponentManage() {
  const [components, setComponents] = useState<ComponentMapItem[]>([])
  const [listLoading, setListLoading] = useState(true)
  const [syncStates, setSyncStates]   = useState<Record<string, SyncState>>({})

  useEffect(() => {
    api.listComponentMap()
      .then(d => setComponents(d.items))
      .catch(() => message.error('加载组件库列表失败'))
      .finally(() => setListLoading(false))
  }, [])

  const handleSync = async (fileKey: string) => {
    setSyncStates(p => ({ ...p, [fileKey]: { loading: true } }))
    try {
      const result: SyncResult = await api.syncComponent(fileKey)
      setSyncStates(p => ({ ...p, [fileKey]: { loading: false, result } }))
    } catch (e) {
      setSyncStates(p => ({
        ...p,
        [fileKey]: { loading: false, error: e instanceof Error ? e.message : String(e) },
      }))
    }
  }

  if (listLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 100 }}><Spin size="large" /></div>
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0f172a' }}>组件集管理</h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
          点击「同步」触发：获取版本 → 下载文件 → 拆解 → 写入数据库 → 向量化
        </p>
      </div>

      {components.length === 0 ? (
        <Alert message="component_map.json 中暂无组件库配置" type="info" showIcon style={{ borderRadius: 10 }} />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {components.map(item => {
            const state = syncStates[item.fileKey]
            const done  = !!state?.result

            return (
              <div
                key={item.fileKey}
                style={{
                  background: '#fff',
                  borderRadius: 14,
                  border: `1px solid ${done ? '#bbf7d0' : '#e2e8f0'}`,
                  overflow: 'hidden',
                  transition: 'border-color 0.3s',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                }}
              >
                {/* Card header */}
                <div
                  style={{
                    padding: '18px 20px 16px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 14,
                    borderBottom: '1px solid #f1f5f9',
                  }}
                >
                  <div
                    style={{
                      width: 40, height: 40, borderRadius: 10,
                      background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', fontSize: 18, flexShrink: 0,
                    }}
                  >
                    <BlockOutlined />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 15, color: '#0f172a' }}>{item.name}</div>
                    <Tag
                      style={{
                        marginTop: 4, fontSize: 11, borderRadius: 4,
                        fontFamily: 'ui-monospace, monospace', color: '#94a3b8',
                        background: '#f8fafc', border: '1px solid #e2e8f0',
                      }}
                    >
                      {item.fileKey}
                    </Tag>
                  </div>
                  <Button
                    type={done ? 'default' : 'primary'}
                    size="small"
                    icon={done
                      ? <CheckCircleFilled style={{ color: '#10b981' }} />
                      : <SyncOutlined spin={state?.loading} />
                    }
                    loading={state?.loading}
                    onClick={() => handleSync(item.fileKey)}
                    style={done ? { borderColor: '#bbf7d0', color: '#10b981' } : {}}
                  >
                    {done ? '已同步' : '同步'}
                  </Button>
                </div>

                {/* Card body */}
                <div style={{ padding: '16px 20px', minHeight: 60 }}>
                  {!state && (
                    <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                      点击「同步」更新此组件库的资源数据
                    </Typography.Text>
                  )}

                  {state?.loading && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#6366f1' }}>
                      <Spin size="small" />
                      <span style={{ fontSize: 13 }}>同步中，请稍候…</span>
                    </div>
                  )}

                  {state?.result && (
                    <Space size={40}>
                      <Statistic
                        title={<span style={{ fontSize: 12, color: '#64748b' }}>新增</span>}
                        value={state.result.added}
                        valueStyle={{ fontSize: 22, fontWeight: 700, color: '#10b981' }}
                      />
                      <Statistic
                        title={<span style={{ fontSize: 12, color: '#64748b' }}>更新</span>}
                        value={state.result.updated}
                        valueStyle={{ fontSize: 22, fontWeight: 700, color: '#6366f1' }}
                      />
                    </Space>
                  )}

                  {state?.error && (
                    <Alert
                      message="同步失败"
                      description={state.error}
                      type="error"
                      showIcon
                      style={{ borderRadius: 8 }}
                    />
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
