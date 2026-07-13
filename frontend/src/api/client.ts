// Thin fetch wrapper: prepends the API base URL and injects the JWT.

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

const TOKEN_KEY = 'refchecks_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      // response body was not JSON; keep statusText
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

// Ping the backend's health endpoint. On Render's free tier the service spins
// down when idle; the first request wakes it, and Render holds that request
// open (often 30-60s) until the container is up — so this resolves true once
// the API is live again. Used by the "Wake backend" control.
export async function wakeBackend(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`, { method: 'GET' })
    return res.ok
  } catch {
    return false
  }
}

export { API_URL }
