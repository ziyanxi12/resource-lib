import { useState, useEffect, useCallback, type ReactNode } from 'react'
import { Modal, List, Tag, Spin, message } from 'antd'
import dayjs from 'dayjs'
import { api, OperationLog } from '../api'

const ACTION_CATEGORY: Record<string, string> = {
  create:              '创建',
  update:              '修改',
  delete:              '删除',
  batch_delete:        '删除',
  batch_clear:         '删除',
  batch_move:          '修改',
  batch_upload:        '创建',
  batch_import:        '创建',
  batch_import_cancel: '修改',
  move:                '修改',
  restore:             '创建',
  vector_sync:         '修改',
  ai_understand:       '修改',
}

const CATEGORY_COLOR: Record<string, string> = {
  创建: 'green',
  修改: 'blue',
  删除: 'red',
}

const TARGET_TYPE_LABEL: Record<string, string> = {
  resource: '资源',
  group: '分组',
  source: '来源',
}

function formatLogText(log: OperationLog): ReactNode {
  const d = log.detail || {}
  const typeLabel = TARGET_TYPE_LABEL[log.target_type] || log.target_type
  const name = log.target_name ?? ''
  const nameEl = <span style={{ color: '#1677ff', fontWeight: 500 }}>{name || '?'}</span>

  switch (log.action) {
    case 'create':
      return <>创建了{typeLabel} {nameEl}</>

    case 'update':
      return <>修改了{typeLabel} {nameEl}</>

    case 'delete': {
      if (log.target_type === 'source') {
        const count = d.deleted_resources ?? 0
        return <>删除了{typeLabel} {nameEl} — 含 {count} 个资源</>
      }
      return <>删除了{typeLabel} {nameEl}</>
    }

    case 'batch_delete': {
      const count = d.count ?? 0
      return <>批量删除了 {count} 个{typeLabel}</>
    }

    case 'batch_clear': {
      const count = d.count ?? 0
      return <>通过清空数据删除了 {count} 个资源</>
    }

    case 'batch_move': {
      const count = d.count ?? 0
      return <>通过批量移动修改了 {count} 个资源</>
    }

    case 'batch_upload': {
      const count = d.count ?? 0
      return <>通过批量上传创建了 {count} 个资源</>
    }

    case 'batch_import': {
      const status = d.status as string | undefined
      const rc = d.resources_created
      if (status === 'success') {
        return <>通过全量导入创建了 {rc ?? 0} 个资源</>
      }
      if (status === 'cancelled') {
        return <>全量导入已取消</>
      }
      if (status === 'failed') {
        return <>全量导入失败 — {String(d.message ?? '')}</>
      }
      return <>全量导入</>
    }

    case 'batch_import_cancel':
      return <>取消了导入任务</>

    case 'move':
      return <>移动了{typeLabel} {nameEl}</>

    case 'restore': {
      const count = d.restored_resources ?? 0
      return <>恢复了{typeLabel} {nameEl} — 含 {count} 个资源</>
    }

    case 'vector_sync': {
      const synced = d.synced ?? 0
      return <>通过向量同步修改了 {synced} 个资源</>
    }

    case 'ai_understand':
      return <>通过语义生成修改了资源 {nameEl}</>

    default:
      return <>{log.action} {typeLabel} {nameEl}</>
  }
}

interface Props {
  sourceId: number | null
  open: boolean
  onClose: () => void
}

export default function OperationLogModal({ sourceId, open, onClose }: Props) {
  const [items, setItems] = useState<OperationLog[]>([])
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    if (!sourceId) return
    setLoading(true)
    try {
      const data = await api.getOperationLogs({
        source_id: sourceId,
        limit: 10000,
      })
      setItems(data.items)
    } catch {
      message.error('加载操作日志失败')
    } finally {
      setLoading(false)
    }
  }, [sourceId])

  useEffect(() => {
    if (open && sourceId) load()
  }, [open, sourceId, load])

  return (
    <Modal
      title="操作日志"
      open={open}
      onCancel={onClose}
      footer={<></>}
      width={720}
      destroyOnClose
    >
      <Spin spinning={loading}>
        <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
          <List
            dataSource={items}
            locale={{ emptyText: '暂无操作记录' }}
            renderItem={(log) => {
              const typeLabel = TARGET_TYPE_LABEL[log.target_type] || log.target_type
              const category = ACTION_CATEGORY[log.action]
              const tagText = category ? `${typeLabel}${category}` : log.action
              const tagColor = category ? CATEGORY_COLOR[category] : 'default'
              return (
                <List.Item style={{ padding: '12px 0', alignItems: 'flex-start' }}>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <Tag color={tagColor} style={{ margin: 0 }}>{tagText}</Tag>
                      <span style={{ fontSize: 13, fontWeight: 500, color: '#1e293b' }}>
                        {log.operator} {log.operator_account}
                      </span>
                      <span style={{ fontSize: 11, color: '#cbd5e1' }}>
                        {log.created_at ? dayjs(log.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, color: '#1e293b', lineHeight: 1.6, marginTop: 4 }}>
                      {formatLogText(log)}
                    </div>
                  </div>
                </List.Item>
              )
            }}
          />
        </div>
      </Spin>
    </Modal>
  )
}
