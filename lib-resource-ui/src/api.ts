const BASE = import.meta.env.VITE_API_BASE ?? ''

export const staticUrl = (path: string) => `${BASE}/static/${path}`

async function request(url: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${url}`, options)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  listResources: (params: {
    type?: string
    page?: number
    limit?: number
    search?: string
    filters?: Record<string, string[] | null | undefined>
    group_id?: number | null
  }) => {
    const q = new URLSearchParams()
    if (params.type) q.set('type', params.type)
    if (params.page) q.set('page', String(params.page))
    if (params.limit) q.set('limit', String(params.limit))
    if (params.search) q.set('search', params.search)
    if (params.group_id) q.set('group_id', String(params.group_id))
    if (params.filters) {
      for (const [key, values] of Object.entries(params.filters)) {
        values?.forEach(v => q.append(key, v))
      }
    }
    return request(`/api/resources?${q}`)
  },

  getFilterOptions: (type: string): Promise<{ options: Record<string, string[]> }> =>
    request(`/api/resources/filter-options?type=${type}`),

  updateResource: (id: number, data: Record<string, unknown>) =>
    request(`/api/resources/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteResource: (id: number) =>
    request(`/api/resources/${id}`, { method: 'DELETE' }),

  listComponentMap: () => request('/api/component/list'),

  syncComponent: (file_key: string) =>
    request('/api/component/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_key }),
    }),

  uploadTemplate: (data: { name: string; description?: string; hex_data: string }) =>
    request('/api/template/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  batchUploadTemplates: (formData: FormData): Promise<{
    success: boolean
    count: number
    items: { id: number; name: string; file_path: string; thumbnail_path: string }[]
    message: string
  }> =>
    request('/api/template/batch-upload', {
      method: 'POST',
      body: formData,
    }),

  syncIcon: () =>
    request('/api/icon/sync', { method: 'POST' }),

  uploadImage: (formData: FormData) =>
    request('/api/image/upload', {
      method: 'POST',
      body: formData,
    }),

  batchUploadImages: (formData: FormData): Promise<{
    success: boolean
    count: number
    items: { id: number; name: string; file_path: string; width?: number; height?: number }[]
    message: string
  }> =>
    request('/api/image/batch-upload', {
      method: 'POST',
      body: formData,
    }),

  uploadFile: (formData: FormData): Promise<{
    id: number
    name: string
    file_path: string
    thumbnail_path: string
    message: string
  }> =>
    request('/api/file/upload', {
      method: 'POST',
      body: formData,
    }),

  batchUploadFiles: (formData: FormData): Promise<{
    success: boolean
    count: number
    items: { id: number; name: string; file_path: string; thumbnail_path: string; message: string }[]
    message: string
  }> =>
    request('/api/file/batch-upload', {
      method: 'POST',
      body: formData,
    }),

  understandImage: (id: number): Promise<{ id: number; description: string }> =>
    request(`/api/resources/${id}/understand`, { method: 'POST' }),

  vectorSearch: async (params: {
    query: string
    type: string
    limit?: number
    filters?: Record<string, unknown>
  }) => {
    const data = await request('/api/vector/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: params.type,
        queries: [params.query],
        top_k: params.limit ?? 50,
        ...(params.filters ? { filters: params.filters } : {}),
      }),
    })
    return (data.results?.[0]) ?? []
  },

  getGroups: (type: string): Promise<{
    resource_type: number
    resource_type_name: string
    items: GroupNode[]
  }> =>
    request(`/api/groups?type=${type}`),

  createGroup: (data: { resource_type: number; name: string; parent_id?: number | null }): Promise<{
    id: number
    name: string
    parent_id: number | null
    level: number
    real_path: string
    sort_order: number
  }> =>
    request('/api/groups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateGroup: (id: number, data: { name: string }): Promise<{ id: number; name: string }> =>
    request(`/api/groups/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteGroup: (id: number): Promise<{ id: number; message: string }> =>
    request(`/api/groups/${id}`, { method: 'DELETE' }),

  moveGroup: (id: number, data: { parent_id?: number | null; sort_order?: number }): Promise<{
    id: number
    parent_id: number | null
    level: number
    real_path: string
    sort_order: number
  }> =>
    request(`/api/groups/${id}/move`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  syncVectors: (type: string): Promise<{
    total: number
    synced: number
    failed: number
    skipped: number
    message: string
  }> =>
    request(`/api/resources/sync-vectors?type=${type}`, { method: 'POST' }),
}

export interface GroupNode {
  id: number
  name: string
  parent_id: number | null
  level: number
  real_path: string
  sort_order: number
  children: GroupNode[]
}
