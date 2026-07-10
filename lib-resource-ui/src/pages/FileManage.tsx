import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'

export default function FileManage() {
  const navigate = useNavigate()
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <ResourceList
      type="file"
      label="文件"
      handleRef={listRef}
      extraActions={
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => navigate('/file/upload')}
          >
            批量上传
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={() => navigate('/file/zip-upload')}
          >
            ZIP批量上传
          </Button>
        </div>
      }
    />
  )
}