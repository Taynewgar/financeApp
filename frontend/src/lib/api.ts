import { supabase } from './supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `Erro ${status}`)
    this.status = status
    this.detail = detail
  }
}

/** Chama a API do backend anexando o token da sessão Supabase atual. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) {
    throw new ApiError(401, 'Sessão expirada — faça login novamente.')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, body?.detail ?? body)
  }
  return body as T
}

/** /health não exige autenticação — usado pra checar se o backend está no ar. */
export async function checkHealth(): Promise<{ status: string; supabase_configured: boolean }> {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new ApiError(response.status, 'Backend indisponível')
  }
  return response.json()
}
