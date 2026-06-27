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
  icon_id?: number | null
  icon_chinese_name?: string | null
  icon_name?: string | null
  icon_english_name?: string | null
  icon_category?: string | null
  cv_domain?: string | null
  cv_canvas_name?: string | null
  cv_component_name?: string | null
  cv_component_guid?: string | null
  cv_component_key?: string | null
  cv_variant_name?: string | null
  cv_variant_guid?: string | null
  cv_variant_key?: string | null
  cv_component_props?: { name: string; type: string }[] | null
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
