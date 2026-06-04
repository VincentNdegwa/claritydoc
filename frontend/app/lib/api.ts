import type {
  DocumentResponse,
  DocumentDetailResponse,
  DocumentCreate,
  DeepAnalysisViewResponse,
  AuditFlagResponse,
  ObligationResponse,
  DocumentRelationshipCreate,
  DocumentRelationshipSuccessResponse,
  AuditFlagCreate,
  AuditFlagStatusUpdate,
  ObligationCreate,
  ObligationStatusUpdate,
} from '@/types/api'

const API_BASE_URL = import.meta.env.NUXT_APP_URL || 'http://localhost:8000'

const fetchWithAuth = async (endpoint: string, options: RequestInit = {}, token: string | null = null) => {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export const useApi = () => {
  return {
    get: <T = any>(endpoint: string, token: string | null) => fetchWithAuth(endpoint, { method: 'GET' }, token) as Promise<T>,
    post: <T = any>(endpoint: string, data: any, token: string | null) => fetchWithAuth(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }, token) as Promise<T>,
    put: <T = any>(endpoint: string, data: any, token: string | null) => fetchWithAuth(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, token) as Promise<T>,
    patch: <T = any>(endpoint: string, data: any, token: string | null) => fetchWithAuth(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }, token) as Promise<T>,
    delete: (endpoint: string, token: string | null) => fetchWithAuth(endpoint, { method: 'DELETE' }, token),
    upload: <T = any>(endpoint: string, formData: FormData, token: string | null) => fetchWithAuth(endpoint, {
      method: 'POST',
      body: formData,
    }, token) as Promise<T>,
  }
}

export const useDocumentApi = () => {
  const api = useApi()

  return {
    upload: (data: DocumentCreate, token: string | null) => {
      const formData = new FormData()
      formData.append('file', data.file)
      formData.append('document_type', data.document_type)
      return api.upload<DocumentResponse>('/api/v1/documents/upload', formData, token)
    },
    list: (token: string | null) => api.get<DocumentResponse[]>('/api/v1/documents', token),
    get: (documentId: string, token: string | null) => api.get<DocumentDetailResponse>(`/api/v1/documents/${documentId}`, token),
    delete: (documentId: string, token: string | null) => api.delete(`/api/v1/documents/${documentId}`, token),
    getAnalysis: (documentId: string, token: string | null) => api.get<DeepAnalysisViewResponse>(`/api/v1/documents/${documentId}/analysis`, token),
  }
}

export const useAuditApi = () => {
  const api = useApi()

  return {
    create: (data: AuditFlagCreate, token: string | null) => api.post<AuditFlagResponse>('/api/v1/audits/', data, token),
    list: (params: { document_version_id?: string; skip?: number; limit?: number }, token: string | null) => {
      const queryString = new URLSearchParams(params as any).toString()
      return api.get<AuditFlagResponse[]>(`/api/v1/audits/${queryString ? `?${queryString}` : ''}`, token)
    },
    get: (auditFlagId: string, token: string | null) => api.get<AuditFlagResponse>(`/api/v1/audits/${auditFlagId}`, token),
    updateStatus: (flagId: string, data: AuditFlagStatusUpdate, token: string | null) => 
      api.patch<AuditFlagResponse>(`/api/v1/audits/flags/${flagId}`, data, token),
  }
}

export const useObligationApi = () => {
  const api = useApi()

  return {
    create: (data: ObligationCreate, token: string | null) => api.post<ObligationResponse>('/api/v1/obligations/', data, token),
    list: (params: { document_id?: string; status?: string; skip?: number; limit?: number }, token: string | null) => {
      const queryString = new URLSearchParams(params as any).toString()
      return api.get<ObligationResponse[]>(`/api/v1/obligations/${queryString ? `?${queryString}` : ''}`, token)
    },
    get: (obligationId: string, token: string | null) => api.get<ObligationResponse>(`/api/v1/obligations/${obligationId}`, token),
    updateStatus: (obligationId: string, data: ObligationStatusUpdate, token: string | null) => 
      api.patch<ObligationResponse>(`/api/v1/obligations/${obligationId}`, data, token),
  }
}

export const useRelationshipApi = () => {
  const api = useApi()

  return {
    create: (data: DocumentRelationshipCreate, token: string | null) => 
      api.post<DocumentRelationshipSuccessResponse>('/api/v1/relationships', data, token),
  }
}
