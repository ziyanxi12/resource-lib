import { useRef, useState } from 'react'
import { Button, message } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import IllusList, { type IllusListHandle } from './IllusList'
import GroupTree from '../components/GroupTree'
import { api } from '../api'

export default function IllustrationManage() {
  const [syncing, setSyncing] = useState(false)
  const listRef = useRef<IllusListHandle | null>(null)
  const [groupId, setGroupId] = useState<number | null>(null)

  const handleSyncVectors = async () => {
    setSyncing(true)
    try {
      const r = await api.syncVectors('illus')
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
        type="illus"
        selectedId={groupId}
        onSelect={setGroupId}
        width={240}
      />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <IllusList
          handleRef={listRef}
          groupId={groupId}
          extraActions={
            <Button
              icon={<SyncOutlined spin={syncing} />}
              loading={syncing}
              onClick={handleSyncVectors}
            >
              向量同步
            </Button>
          }
        />
      </div>
    </div>
  )
}
