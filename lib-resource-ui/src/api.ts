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
  }) => {
    const q = new URLSearchParams()
    if (params.type) q.set('type', params.type)
    if (params.page) q.set('page', String(params.page))
    if (params.limit) q.set('limit', String(params.limit))
    if (params.search) q.set('search', params.search)
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

  syncIcon: () =>
    request('/api/icon/sync', { method: 'POST' }),

  uploadImage: (formData: FormData) =>
    request('/api/image/upload', {
      method: 'POST',
      body: formData,
    }),

  vectorSearch: async (params: { query: string; type: string; limit?: number }) => {
    const data = await request('/api/vector/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: params.type,
        queries: [params.query],
        top_k: params.limit ?? 50,
      }),
    })
    return (data.results?.[0]) ?? []
  },
}
