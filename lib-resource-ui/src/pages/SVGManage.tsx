import { useState, useRef } from 'react'
import { Button, message } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import IconList, { type IconListHandle } from './IconList'
import GroupTree from '../components/GroupTree'
import { api } from '../api'

export default function SVGManage() {
  // const [syncing, setSyncing] = useState(false)
  const [syncingVectors, setSyncingVectors] = useState(false)
  const listRef = useRef<IconListHandle | null>(null)
  const [groupId, setGroupId] = useState<number | null>(null)

  // const handleSync = async () => {
  //   setSyncing(true)
  //   try {
  //     const r = await api.syncIcon()
  //     message.success(`同步完成：新增 ${r.added}，更新 ${r.updated}`)
  //     listRef.current?.refresh()
  //   } catch (e) {
  //     message.error(e instanceof Error ? e.message : '同步失败')
  //   } finally {
  //     setSyncing(false)
  //   }
  // }

  const handleSyncVectors = async () => {
    setSyncingVectors(true)
    try {
      const r = await api.syncVectors('icon')
      message.success(r.message)
      listRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '向量同步失败')
    } finally {
      setSyncingVectors(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
      <GroupTree
        type="icon"
        selectedId={groupId}
        onSelect={setGroupId}
        width={240}
      />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <IconList
          type="icon"
          label="图标"
          handleRef={listRef}
          groupId={groupId}
          extraActions={
            <Button
              icon={<SyncOutlined spin={syncingVectors} />}
              loading={syncingVectors}
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
