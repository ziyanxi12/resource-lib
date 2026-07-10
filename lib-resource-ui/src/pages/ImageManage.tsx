import { useState, useRef } from 'react'
import { Button } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import BatchUploadModal from './BatchUploadModal'

export default function ImageManage() {
  const [batchModalOpen, setBatchModalOpen] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <>
      <ResourceList
        type="image"
        label="图片"
        handleRef={listRef}
        extraActions={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setBatchModalOpen(true)}
          >
            批量上传
          </Button>
        }
      />
      <BatchUploadModal
        open={batchModalOpen}
        onClose={() => setBatchModalOpen(false)}
        onSuccess={() => listRef.current?.refresh()}
      />
    </>
  )
}