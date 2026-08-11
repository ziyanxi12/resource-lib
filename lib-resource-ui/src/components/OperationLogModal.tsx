import { useState, useEffect, useCallback } from 'react'
import { Modal, List, Tag, Spin, message } from 'antd'
import dayjs from 'dayjs'
import { api, OperationLog } from '../api'

const ACTION_META: Record<string, { label: string; color: string }> = {
  create:               { label: '创建',       color: 'green'   },
  update:               { label: '修改',       color: 'blue'    },
  delete:               { label: '删除',       color: 'red'     },
  batch_delete:         { label: '批量删除',   color: 'red'     },
  batch_clear:          { label: '清空分组',   color: 'red'     },
  batch_move:           { label: '批量移动',   color: 'purple'  },
  batch_upload:         { label: '批量上传',   color: 'cyan'    },
  batch_import:         { label: '全量导入',   color: 'cyan'    },
  batch_import_cancel:  { label: '取消导入',   color: 'orange'  },
  move:                 { label: '移动',       color: 'purple'  },
  restore:              { label: '恢复',       color: 'green'   },
  vector_sync:          { label: '向量同步',   color: 'gold'    },
  ai_understand:        { label: '语义生成',   color: 'geekblue'},
}

const TARGET_TYPE_LABEL: Record<string, string> = {
  resource: '资源',
  group: '分组',
  source: '来源',
}

function formatLogText(log: OperationLog): string {
  const d = log.detail || {}
  const typeLabel = TARGET_TYPE_LABEL[log.target_type] || log.target_type

  const idStr = log.target_id != null ? String(log.target_id) : ''
  const nameStr = log.target_name ?? ''

  let subject: string
  if (log.target_type === 'group') {
    subject = `分组 ID: ${idStr || '?'} 分组名: ${nameStr || '?'}`
  } else if (log.target_type === 'resource') {
    const gid = d.group_id
    subject = `资源 ID: ${idStr || '?'} 资源名: ${nameStr || '?'} 位于分组 ID: ${gid != null ? String(gid) : '无'}`
  } else if (log.target_type === 'source') {
    subject = `来源「${nameStr || '?'}」`
  } else {
    subject = `${typeLabel}「${nameStr}」`
  }

  switch (log.action) {
    case 'create':
      return `创建了${subject}`

    case 'update':
      return `修改了${subject}`

    case 'delete':
      return `删除了${subject}`

    case 'batch_delete': {
      const count = d.count ?? 0
      return `批量删除了 ${count} 个${typeLabel}`
    }

    case 'batch_clear': {
      const count = d.count ?? 0
      const filters = d.filters as Record<string, unknown> | undefined
      const gid = filters?.group_id
      return `清空分组 ID: ${gid ?? '?'} — 删除了 ${count} 个${typeLabel}`
    }

    case 'batch_move': {
      const count = d.count ?? 0
      const gid = d.target_group_id
      return `批量移动了 ${count} 个${typeLabel}到分组 ID: ${gid ?? '?'}`
    }

    case 'batch_upload': {
      const count = d.count ?? 0
      return `批量上传了 ${count} 个${typeLabel}`
    }

    case 'batch_import': {
      const status = d.status as string | undefined
      const gc = d.groups_created
      const rc = d.resources_created
      if (status === 'success') {
        return `全量导入完成 — 分组 ${gc ?? 0} 个, 资源 ${rc ?? 0} 个`
      }
      if (status === 'cancelled') {
        return `全量导入已取消`
      }
      if (status === 'failed') {
        return `全量导入失败 — ${d.message ?? ''}`
      }
      return `全量导入`
    }

    case 'batch_import_cancel':
      return `取消了导入任务 (task: ${d.task_id ?? ''})`

    case 'move':
      return `移动了${subject}`

    case 'restore':
      return `恢复了${subject}`

    case 'vector_sync': {
      const synced = d.synced ?? 0
      const skipped = d.skipped ?? 0
      return `向量同步 — 同步: ${synced}, 跳过: ${skipped}`
    }

    case 'ai_understand':
      return `生成了${subject}的语义描述`

    default:
      return `${log.action} ${subject}`
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
              const meta = ACTION_META[log.action]
              return (
                <List.Item style={{ padding: '12px 0', alignItems: 'flex-start' }}>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      {meta && <Tag color={meta.color} style={{ margin: 0 }}>{meta.label}</Tag>}
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
