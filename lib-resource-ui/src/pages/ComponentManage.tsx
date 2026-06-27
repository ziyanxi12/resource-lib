import { useState, useEffect, useRef } from 'react'
import { Button, Modal, Alert, Spin, Space, Statistic, Tag, message } from 'antd'
import { SyncOutlined, BlockOutlined, CheckCircleFilled, SettingOutlined } from '@ant-design/icons'
import ComponentList, { type ComponentListHandle } from './ComponentList'
import { api } from '../api'
import type { ComponentMapItem, SyncResult } from '../types'

type SyncState = { loading: boolean; result?: SyncResult; error?: string }

function SyncModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [components, setComponents] = useState<ComponentMapItem[]>([])
  const [listLoading, setListLoading] = useState(true)
  const [syncStates, setSyncStates] = useState<Record<string, SyncState>>({})

  useEffect(() => {
    if (!open) return
    setListLoading(true)
    api.listComponentMap()
      .then(d => setComponents(d.items))
      .catch(() => message.error('加载组件库列表失败'))
      .finally(() => setListLoading(false))
  }, [open])

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

  return (
    <Modal
      title="同步组件库"
      open={open}
      onCancel={onClose}
      footer={null}
      width={640}
      destroyOnClose
    >
      {listLoading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}><Spin /></div>
      ) : components.length === 0 ? (
        <Alert message="component_map.json 中暂无组件库配置" type="info" showIcon />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
          {components.map(item => {
            const state = syncStates[item.fileKey]
            const done = !!state?.result
            return (
              <div
                key={item.fileKey}
                style={{
                  background: done ? '#f0fdf4' : '#f8fafc',
                  borderRadius: 10,
                  border: `1px solid ${done ? '#bbf7d0' : '#e2e8f0'}`,
                  padding: '14px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  transition: 'border-color 0.3s',
                }}
              >
                <div
                  style={{
                    width: 36, height: 36, borderRadius: 9,
                    background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontSize: 16, flexShrink: 0,
                  }}
                >
                  <BlockOutlined />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, color: '#0f172a' }}>{item.name}</div>
                  <Tag
                    style={{
                      marginTop: 2, fontSize: 11, borderRadius: 4,
                      fontFamily: 'ui-monospace,monospace', color: '#94a3b8',
                      background: '#fff', border: '1px solid #e2e8f0',
                    }}
                  >
                    {item.fileKey}
                  </Tag>
                </div>
                {state?.result && (
                  <Space size={24} style={{ flexShrink: 0 }}>
                    <Statistic
                      title={<span style={{ fontSize: 11 }}>新增</span>}
                      value={state.result.added}
                      valueStyle={{ fontSize: 18, fontWeight: 700, color: '#10b981' }}
                    />
                    <Statistic
                      title={<span style={{ fontSize: 11 }}>更新</span>}
                      value={state.result.updated}
                      valueStyle={{ fontSize: 18, fontWeight: 700, color: '#6366f1' }}
                    />
                  </Space>
                )}
                {state?.error && (
                  <span style={{ fontSize: 12, color: '#ef4444', maxWidth: 160 }}>{state.error}</span>
                )}
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
            )
          })}
        </div>
      )}
    </Modal>
  )
}

export default function ComponentManage() {
  const [modalOpen, setModalOpen] = useState(false)
  const listRef = useRef<ComponentListHandle | null>(null)

  return (
    <>
      <ComponentList
        handleRef={listRef}
        extraActions={
          <Button
            icon={<SettingOutlined />}
            onClick={() => setModalOpen(true)}
          >
            同步组件库
          </Button>
        }
      />
      <SyncModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          listRef.current?.refresh()
        }}
      />
    </>
  )
}
