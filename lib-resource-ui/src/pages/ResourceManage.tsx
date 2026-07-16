import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Select, message, Modal } from 'antd'
import { UploadOutlined, SyncOutlined, DeleteOutlined, FileZipOutlined } from '@ant-design/icons'
import ResourceTable, { type ResourceTableHandle } from '../components/ResourceTable'
import GroupTree from '../components/GroupTree'
import { api, Source } from '../api'

const RESOURCE_TYPE_MAP: Record<string, number> = {
  component: 1,
  template: 2,
  icon: 3,
  illus: 4,
  image: 5,
  file: 6,
}

export default function ResourceManage() {
  const { type = 'component' } = useParams<{ type: string }>()
  const navigate = useNavigate()
  const tableRef = useRef<ResourceTableHandle | null>(null)
  const [groupId, setGroupId] = useState<number | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [clearModalOpen, setClearModalOpen] = useState(false)

  useEffect(() => {
    api.getSources()
      .then(data => {
        const typeNum = RESOURCE_TYPE_MAP[type]
        const filtered = data.items.filter(s => s.resource_type === typeNum)
        setSources(filtered)
        if (filtered.length > 0) {
          setSourceId(filtered[0].id)
        } else {
          setSourceId(null)
        }
      })
      .catch(() => message.error('加载来源失败'))
  }, [type])

  useEffect(() => {
    setGroupId(null)
  }, [type, sourceId])

  const handleSyncVectors = async () => {
    setSyncing(true)
    try {
      const r = await api.syncVectors(type)
      message.success(r.message)
      tableRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '向量同步失败')
    } finally {
      setSyncing(false)
    }
  }

  const handleClear = async () => {
    setClearing(true)
    try {
      const r = await api.clearResources(type, sourceId, groupId)
      message.success(`已删除 ${r.deleted} 条数据`)
      setClearModalOpen(false)
      tableRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '清空失败')
    } finally {
      setClearing(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
      {/* 左侧栏：来源选择 + 分组树 */}
      <div style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{
          background: '#fff', borderRadius: 8, padding: 12,
          border: '1px solid #e2e8f0',
        }}>
          <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8, fontWeight: 500 }}>
            来源
          </div>
          <Select
            value={sourceId}
            onChange={setSourceId}
            options={sources.map(s => ({ value: s.id, label: s.name }))}
            placeholder="选择来源"
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <GroupTree
            type={type}
            selectedId={groupId}
            onSelect={setGroupId}
            sourceId={sourceId}
            width={280}
          />
        </div>
      </div>

      {/* 右侧：表格 */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <ResourceTable
          type={type}
          sourceId={sourceId}
          groupId={groupId}
          handleRef={tableRef}
          extraActions={
            <>
              {sourceId && (
                <>
                  <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={() => navigate(`/${type}/upload?sourceId=${sourceId}`)}
                  >
                    批量上传
                  </Button>
                  <Button
                    type="primary"
                    icon={<FileZipOutlined />}
                    onClick={() => navigate(`/${type}/upload?mode=zip&sourceId=${sourceId}`)}
                  >
                    ZIP上传
                  </Button>
                </>
              )}
              <Button
                icon={<SyncOutlined spin={syncing} />}
                loading={syncing}
                onClick={handleSyncVectors}
              >
                向量同步
              </Button>
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={() => setClearModalOpen(true)}
              >
                清空数据
              </Button>
            </>
          }
        />
      </div>

      <Modal
        open={clearModalOpen}
        title="确认清空"
        onCancel={() => setClearModalOpen(false)}
        onOk={handleClear}
        okText="确认清空"
        okButtonProps={{ danger: true, loading: clearing }}
      >
        <p>确定清空当前筛选条件下的所有数据吗？</p>
        <p style={{ color: '#64748b', fontSize: 12 }}>
          类型：{type}
          {sourceId && ` | 来源ID: ${sourceId}`}
          {groupId && ` | 分组ID: ${groupId}`}
        </p>
      </Modal>
    </div>
  )
}