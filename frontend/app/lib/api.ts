const API_BASE_URL = import.meta.env.NUXT_APP_URL || 'http://localhost:8000'

export const useApi = () => {
  const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
    // Get the JWT token from Clerk
    // @ts-ignore - Clerk is available globally after initialization
    const clerk = window.Clerk
    const token = await clerk?.session?.getToken?.()
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  return {
    get: (endpoint: string) => fetchWithAuth(endpoint, { method: 'GET' }),
    post: (endpoint: string, data: any) => fetchWithAuth(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    put: (endpoint: string, data: any) => fetchWithAuth(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    delete: (endpoint: string) => fetchWithAuth(endpoint, { method: 'DELETE' }),
  }
}
