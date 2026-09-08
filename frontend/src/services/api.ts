import axios from 'axios'

export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ||
  'http://localhost:8000'

/**
 * Optional admin token, used only when the backend is not running on the same
 * machine as the browser (AVE_ADMIN_TOKEN set on the server).
 *
 * It is kept in sessionStorage, not localStorage: it disappears when the tab
 * closes, and it is never written into the source or into a build artifact.
 */
const ADMIN_TOKEN_STORAGE_KEY = 'ave.adminToken'

export function getAdminToken(): string {
  try {
    return sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

export function setAdminToken(token: string): void {
  try {
    if (token) sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token)
    else sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY)
  } catch {
    /* storage blocked — requests simply go out unauthenticated */
  }
}

export const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = getAdminToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers['X-Admin-Token'] = token
  }
  return config
})

/** Pull a readable message out of an axios/FastAPI error. */
export function errorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
    if (error.code === 'ERR_NETWORK') {
      return `Não consegui falar com o backend em ${API_URL}. Ele está rodando?`
    }
  }
  return fallback
}

// --- Types mirroring backend/app/models/settings_schemas.py -----------------

export interface CredentialStatus {
  configured: boolean
  source: 'vault' | 'env' | 'local' | null
  masked: string | null
  updated_at: string | null
}

export interface ModelInfo {
  id: string
  label: string
  note: string
  free: boolean
}

export interface ProviderInfo {
  id: string
  label: string
  tagline: string
  env_var: string
  key_url: string
  docs_url: string
  key_prefix: string
  requires_key: boolean
  free_tier: boolean
  free_note: string
  recommended: boolean
  analysis_ready: boolean
  tags: string[]
  models: ModelInfo[]
  credential: CredentialStatus
}

export interface ActiveSelection {
  active_provider: string | null
  active_model: string | null
}

export interface VaultInfo {
  encrypted: boolean
  algorithm: string
  location: string
  master_key_source: 'env' | 'file'
  writable: boolean
}

export interface IntegrationsResponse {
  providers: ProviderInfo[]
  active: ActiveSelection
  vault: VaultInfo
}

export interface TestResult {
  provider: string
  ok: boolean
  message: string
  status_code: number | null
}

// --- Settings endpoints ----------------------------------------------------

const settings = '/api/v1/settings'

export async function fetchIntegrations(): Promise<IntegrationsResponse> {
  const { data } = await api.get<IntegrationsResponse>(`${settings}/integrations`)
  return data
}

export async function saveProviderKey(
  providerId: string,
  apiKey: string,
  verify = true
): Promise<{ credential: CredentialStatus; verified: boolean; message: string }> {
  const { data } = await api.put(`${settings}/providers/${providerId}/key`, {
    api_key: apiKey,
    verify,
  })
  return data
}

export async function deleteProviderKey(providerId: string): Promise<void> {
  await api.delete(`${settings}/providers/${providerId}/key`)
}

export async function testProviderKey(
  providerId: string,
  apiKey?: string
): Promise<TestResult> {
  const { data } = await api.post<TestResult>(
    `${settings}/providers/${providerId}/test`,
    apiKey ? { api_key: apiKey } : {}
  )
  return data
}

export async function setActiveModel(
  providerId: string,
  modelId: string
): Promise<ActiveSelection> {
  const { data } = await api.put<ActiveSelection>(`${settings}/active-model`, {
    provider: providerId,
    model: modelId,
  })
  return data
}
