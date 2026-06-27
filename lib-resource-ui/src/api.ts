async function request(url: string, options?: RequestInit) {
  const res = await fetch(url, options)
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
  }) => {
    const q = new URLSearchParams()
    if (params.type) q.set('type', params.type)
    if (params.page) q.set('page', String(params.page))
    if (params.limit) q.set('limit', String(params.limit))
    if (params.search) q.set('search', params.search)
    return request(`/api/resources?${q}`)
  },

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

  syncIcon: (type: 'svg' | 'illustration') =>
    request('/api/icon/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type }),
    }),

  uploadImage: (formData: FormData) =>
    request('/api/image/upload', {
      method: 'POST',
      body: formData,
    }),

  vectorSearch: async (params: { query: string; type: string; limit?: number }) => {
    const typeMap: Record<string, string> = {
      component_set: 'component',
      svg: 'icon',
      illustration: 'icon',
    }
    const data = await request('/api/vector/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: typeMap[params.type] ?? params.type,
        query: params.query,
        top_k: params.limit ?? 50,
      }),
    })
    return data.results ?? []
  },
}
