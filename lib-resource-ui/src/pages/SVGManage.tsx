import { useState, useRef } from 'react'
import { Button, message } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import { api } from '../api'

export default function SVGManage() {
  const [syncing, setSyncing] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)

  const handleSync = async () => {
    setSyncing(true)
    try {
      const r = await api.syncIcon('svg')
      message.success(`同步完成：新增 ${r.added}，更新 ${r.updated}`)
      listRef.current?.refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '同步失败')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <ResourceList
      type="svg"
      label="图标"
      handleRef={listRef}
      extraActions={
        <Button
          type="primary"
          icon={<SyncOutlined spin={syncing} />}
          loading={syncing}
          onClick={handleSync}
        >
          同步图标
        </Button>
      }
    />
  )
}
