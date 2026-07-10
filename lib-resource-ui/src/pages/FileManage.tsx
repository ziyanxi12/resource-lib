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
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => navigate('/file/upload')}
        >
          批量上传
        </Button>
      }
    />
  )
}