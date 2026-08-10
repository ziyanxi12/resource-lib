import { useState, useEffect, useCallback } from 'react'
import { Modal, List, Tag, Pagination, Spin, message } from 'antd'
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
  const name = log.target_name ? `「${log.target_name}」` : ''
  const typeLabel = TARGET_TYPE_LABEL[log.target_type] || log.target_type

  switch (log.action) {
    case 'create':
      return `创建了${typeLabel}${name}`

    case 'update': {
      const fields = d.fields as string[] | undefined
      return `修改了${typeLabel}${name}${fields ? ` — 字段: ${fields.join(', ')}` : ''}`
    }

    case 'delete':
      return `删除了${typeLabel}${name}`

    case 'batch_delete': {
      const count = d.count ?? 0
      return `批量删除了 ${count} 个${typeLabel}`
    }

    case 'batch_clear': {
      const count = d.count ?? 0
      return `清空分组删除了 ${count} 个${typeLabel}`
    }

    case 'batch_move': {
      const count = d.count ?? 0
      const gid = d.target_group_id
      return `批量移动了 ${count} 个${typeLabel}到分组 #${gid ?? '?'}`
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
        return `全量导入完成 — 分组: ${gc ?? 0}, 资源: ${rc ?? 0}`
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
      return `移动了${typeLabel}${name}`

    case 'restore':
      return `恢复了${typeLabel}${name}`

    case 'vector_sync': {
      const synced = d.synced ?? 0
      const skipped = d.skipped ?? 0
      return `向量同步 — 同步: ${synced}, 跳过: ${skipped}`
    }

    case 'ai_understand':
      return `生成了${typeLabel}${name}的语义描述`

    default:
      return `${log.action} ${typeLabel}${name}`
  }
}

interface Props {
  sourceId: number | null
  open: boolean
  onClose: () => void
}

export default function OperationLogModal({ sourceId, open, onClose }: Props) {
  const [items, setItems] = useState<OperationLog[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(20)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    if (!sourceId) return
    setLoading(true)
    try {
      const data = await api.getOperationLogs({
        source_id: sourceId,
        page,
        limit,
      })
      setItems(data.items)
      setTotal(data.total)
    } catch {
      message.error('加载操作日志失败')
    } finally {
      setLoading(false)
    }
  }, [sourceId, page, limit])

  useEffect(() => {
    if (open && sourceId) {
      setPage(1)
      load()
    }
  }, [open, sourceId])

  useEffect(() => {
    if (open && sourceId) load()
  }, [page, limit, open, sourceId, load])

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
        <List
          dataSource={items}
          locale={{ emptyText: '暂无操作记录' }}
          renderItem={(log) => {
            const meta = ACTION_META[log.action]
            return (
              <List.Item style={{ padding: '12px 0', alignItems: 'flex-start' }}>
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, flexWrap: 'wrap' }}>
                    {meta && <Tag color={meta.color} style={{ margin: 0 }}>{meta.label}</Tag>}
                    <span style={{ fontSize: 13, fontWeight: 500, color: '#1e293b' }}>
                      {log.operator} {log.operator_account}
                    </span>
                    <span style={{ fontSize: 13, color: '#1e293b', lineHeight: 1.6 }}>
                      {formatLogText(log)}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: '#cbd5e1', marginTop: 2 }}>
                    {log.created_at ? dayjs(log.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                  </div>
                </div>
              </List.Item>
            )
          }}
        />

        {total > 0 && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
            <Pagination
              current={page}
              pageSize={limit}
              total={total}
              onChange={setPage}
              onShowSizeChange={(_, size) => { setPage(1); setLimit(size) }}
              pageSizeOptions={['10', '20', '50']}
              showTotal={t => `共 ${t} 条`}
              showSizeChanger
              size="small"
            />
          </div>
        )}
      </Spin>
    </Modal>
  )
}
