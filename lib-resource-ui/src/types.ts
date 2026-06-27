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
  raw_data: string | null
  created_by: string | null
  sort_order: number
  created_at: string | null
  updated_at: string | null
  tags: string[]
  score?: number
  vector_text?: string | null
}

export interface ComponentRawData {
  domain: string | null
  canvasName: string | null
  componentKey: string | null
  componentGuid: string | null
  componentName: string | null
  variantName: string | null
  variantKey: string | null
  variantGuid: string | null
  parentKey: string | null
  componentProps: { name: string; type: string }[]
}

export interface IconRawData {
  id: number
  name: string
  englishName: string | null
  category: string | null
  description: string | null
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
