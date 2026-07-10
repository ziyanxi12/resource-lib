import { useState, useRef } from 'react'
import { Button } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'
import BatchUploadTemplateModal from './BatchUploadTemplateModal'

export default function TemplateManage() {
  const [batchModalOpen, setBatchModalOpen] = useState(false)
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <>
      <ResourceList
        type="template"
        label="模版"
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
      <BatchUploadTemplateModal
        open={batchModalOpen}
        onClose={() => setBatchModalOpen(false)}
        onSuccess={() => listRef.current?.refresh()}
      />
    </>
  )
}