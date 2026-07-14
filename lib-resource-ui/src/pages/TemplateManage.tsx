import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, message } from 'antd'
import { UploadOutlined, SyncOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import GroupTree from '../components/GroupTree'
import { api } from '../api'

export default function TemplateManage() {
  const navigate = useNavigate()
  const [syncing, setSyncing] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)
  const [groupId, setGroupId] = useState<number | null>(null)

  const handleSyncVectors = async () => {
    setSyncing(true)
    try {
      const r = await api.syncVectors('template')
      message.success(r.message)
      listRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '向量同步失败')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
      <GroupTree
        type="template"
        selectedId={groupId}
        onSelect={setGroupId}
        width={240}
      />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <ResourceList
          type="template"
          label="模版"
          handleRef={listRef}
          groupId={groupId}
          extraActions={
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={() => navigate('/template/upload')}
              >
                批量上传
              </Button>
              <Button
                icon={<SyncOutlined spin={syncing} />}
                loading={syncing}
                onClick={handleSyncVectors}
              >
                向量同步
              </Button>
            </div>
          }
        />
      </div>
    </div>
  )
}