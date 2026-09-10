/**
 * Minimal API client for the NewwwRecipe FastAPI adapter.
 *
 * Base path is `/api` — in development Vite proxies it to the backend, in production the backend
 * serves `web/dist` directly. No key, token or secret is ever handled here.
 */
import type { GenerateRequest, GenerateResponse, HealthResponse } from '../types'

export const API_BASE = '/api'

export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

/** Pull a human-readable message out of a FastAPI error payload. */
function readDetail(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object') {
    const detail = (payload as { detail?: unknown }).detail
    if (typeof detail === 'string' && detail.trim()) return detail
    if (Array.isArray(detail)) {
      const first = detail[0]
      if (first && typeof first === 'object' && typeof (first as { msg?: string }).msg === 'string') {
        return (first as { msg: string }).msg
      }
    }
  }
  return fallback
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch (err) {
    // Network level failure (backend down / offline) — surfaced as a real error, never faked.
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError(0, 'Cannot reach the kitchen. Is the backend running?')
  }

  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = null
    }
  }
  if (!response.ok) {
    throw new ApiError(response.status, readDetail(payload, `Request failed (${response.status})`))
  }
  return payload as T
}

export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/health', signal ? { signal } : undefined)
}

export function generateRecipe(
  body: GenerateRequest,
  signal?: AbortSignal,
): Promise<GenerateResponse> {
  return requestJson<GenerateResponse>('/recipes/generate', {
    method: 'POST',
    body: JSON.stringify(body),
    ...(signal ? { signal } : {}),
  })
}
