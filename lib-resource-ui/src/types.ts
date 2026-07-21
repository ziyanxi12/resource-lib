export interface Resource {
  id: number
  resource_type: number
  resource_type_name: string
  source_id: number
  name: string
  description: string | null
  search_text: string | null
  vector_text: string | null
  file_name: string | null
  file_path: string | null
  file_size: number | null
  file_type: string | null
  width: number | null
  height: number | null
  thumbnail_path: string | null
  raw_data: Record<string, any> | null
  group_id: number | null
  group_path: string | null
  created_by: string | null
  created_at: number | null
  updated_at: number | null
  data_updated_at: number | null
  vector_updated_at: number | null
  tags: string[]
  score?: number
}

export interface ResourceListResponse {
  total: number
  page: number
  limit: number
  items: Resource[]
}

export interface Source {
  id: number
  code: string
  name: string
  resource_type: number
  is_sync_source: boolean
  config: string | null
  is_active: boolean
  created_at: number
  updated_at: number
}
