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

export interface Source {
  id: number
  name: string
  resource_type: number
  is_sync_source: boolean
  config: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ResourceTypeItem {
  id: number
  name: string
  label: string
}

export const api = {
  getResourceTypes: (): Promise<{ items: ResourceTypeItem[] }> =>
    request('/api/resource-types'),

  getSources: (params?: { type?: string; is_active?: number }): Promise<{ items: Source[] }> => {
    const q = new URLSearchParams()
    if (params?.type) q.set('type', params.type)
    if (params?.is_active !== undefined) q.set('is_active', String(params.is_active))
    return request(`/api/sources?${q}`)
  },

  createSource: (data: {
    name: string
    type: string
    is_sync_source: number
    is_active: number
  }): Promise<Source> =>
    request('/api/sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateSource: (id: number, data: { name: string }): Promise<Source> =>
    request(`/api/sources/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteSource: (id: number): Promise<{ message: string }> =>
    request(`/api/sources/${id}`, { method: 'DELETE' }),

  getTrashSources: (params?: { type?: string }): Promise<{ items: Source[] }> => {
    const q = new URLSearchParams()
    if (params?.type) q.set('type', params.type)
    return request(`/api/sources/trash?${q}`)
  },

  restoreSource: (id: number): Promise<Source> =>
    request(`/api/sources/${id}/restore`, { method: 'POST' }),

  listResources: (params: {
    type?: string
    page?: number
    limit?: number
    search?: string
    group_id?: number | null
    source_id?: number | null
  }) => {
    const q = new URLSearchParams()
    if (params.type) q.set('type', params.type)
    if (params.page) q.set('page', String(params.page))
    if (params.limit) q.set('limit', String(params.limit))
    if (params.search) q.set('search', params.search)
    if (params.group_id) q.set('group_id', String(params.group_id))
    if (params.source_id) q.set('source_id', String(params.source_id))
    return request(`/api/resources?${q}`)
  },

  updateResource: (id: number, data: Record<string, unknown> | FormData) => {
    if (data instanceof FormData) {
      return request(`/api/resources/${id}`, {
        method: 'PUT',
        body: data,
      })
    }
    return request(`/api/resources/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  },

  deleteResource: (id: number) =>
    request(`/api/resources/${id}`, { method: 'DELETE' }),

  batchUpload: (type: string, formData: FormData): Promise<{
    success: boolean
    count: number
    items: { id: number; name: string; file_path: string; thumbnail_path: string }[]
    message: string
  }> =>
    request(`/api/upload?type=${type}`, {
      method: 'POST',
      body: formData,
    }),

  understandImage: (id: number, prompt?: string): Promise<{ id: number; description: string }> => {
    if (prompt) {
      return request(`/api/resources/${id}/understand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })
    }
    return request(`/api/resources/${id}/understand`, { method: 'POST' })
  },

  updateThumbnail: (id: number, formData: FormData): Promise<{ message: string }> =>
    request(`/api/resources/${id}/thumbnail`, {
      method: 'PUT',
      body: formData,
    }),

  updateFile: (id: number, formData: FormData): Promise<{ message: string }> =>
    request(`/api/resources/${id}/file`, {
      method: 'PUT',
      body: formData,
    }),

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

  getGroups: (type: string, sourceId?: number | null, excludeDefault?: boolean): Promise<{
    resource_type: number
    resource_type_name: string
    items: GroupNode[]
  }> => {
    const q = new URLSearchParams()
    q.set('type', type)
    if (sourceId) q.set('source_id', String(sourceId))
    if (excludeDefault !== undefined) q.set('exclude_default', String(excludeDefault))
    return request(`/api/groups?${q}`)
  },

  createGroup: (data: { type: string; name: string; parent_id?: number | null; source_id?: number }): Promise<{
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

  getGroupResourceCount: (groupId: number): Promise<{ count: number }> =>
    request(`/api/groups/${groupId}/resource-count`),

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

  syncVectors: (type: string, sourceId?: number | null): Promise<{
    total: number
    synced: number
    failed: number
    skipped: number
    message: string
  }> => {
    const q = new URLSearchParams()
    q.set('type', type)
    if (sourceId) q.set('source_id', String(sourceId))
    return request(`/api/resources/sync-vectors?${q}`, { method: 'POST' })
  },

  cleanupOrphanGroups: (): Promise<{ deleted: number; message: string }> =>
    request('/api/init/cleanup-orphan-groups', { method: 'POST' }),

  clearResources: (type: string, sourceId?: number | null, groupId?: number | null): Promise<{ deleted: number }> => {
    const q = new URLSearchParams()
    q.set('type', type)
    if (sourceId) q.set('source_id', String(sourceId))
    if (groupId) q.set('group_id', String(groupId))
    return request(`/api/resources/batch?${q}`, { method: 'DELETE' })
  },

  batchDeleteResources: (ids: number[], type: string): Promise<{ deleted: number }> =>
    request('/api/resources/batch-ids', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, type }),
    }),

  batchMoveResources: (ids: number[], groupId: number, type: string): Promise<{ moved: number }> =>
    request('/api/resources/batch-move', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, group_id: groupId, type }),
    }),
}

export interface GroupNode {
  id: number
  name: string
  parent_id: number | null
  level: number
  real_path: string
  sort_order: number
  is_default: number
  resource_count: number
  children: GroupNode[]
}
