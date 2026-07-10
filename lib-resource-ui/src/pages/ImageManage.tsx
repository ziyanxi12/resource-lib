import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import ResourceList, { type ResourceListHandle } from './ResourceList'

export default function ImageManage() {
  const navigate = useNavigate()
  const listRef = useRef<ResourceListHandle | null>(null)

  return (
    <ResourceList
      type="image"
      label="图片"
      handleRef={listRef}
      extraActions={
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => navigate('/image/upload')}
        >
          批量上传
        </Button>
      }
    />
  )
}