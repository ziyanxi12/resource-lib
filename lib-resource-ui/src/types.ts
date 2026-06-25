export interface Resource {
  id: number
  resource_type: number
  resource_type_name: string
  name: string
  file_name: string | null
  file_path: string | null
  thumbnail_path: string | null
  file_size: number | null
  mime_type: string | null
  dimensions: { width: number; height: number } | null
  description: string | null
  raw_data: string | null        // JSON 字符串，前端按需 parse
  created_by: string | null
  sort_order: number
  created_at: string | null
  updated_at: string | null
  tags: string[]
}

export interface ResourceListResponse {
  total: number
  page: number
  limit: number
  items: Resource[]
}

export interface ComponentMapItem {
  fileKey: string
  name: string
}

export interface SyncResult {
  added: number
  updated: number
  message: string
}
