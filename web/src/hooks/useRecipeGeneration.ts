import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, generateRecipe } from '../api/client'
import type { GenerateRequest, GenerateResponse } from '../types'

export const LOADING_MESSAGES = [
  'Finding flavor bridges…',
  'Testing the creative leap…',
  'Checking whether it can actually be cooked…',
  'Scoring the idea with CIE…',
] as const

export type GenerationStatus = 'idle' | 'loading' | 'success' | 'error'

export interface GenerationState {
  status: GenerationStatus
  data: GenerateResponse | null
  error: string | null
  messageIndex: number
}

export interface UseRecipeGeneration extends GenerationState {
  start: (body: GenerateRequest) => void
  cancel: () => void
  retry: () => void
  reset: () => void
}

const MESSAGE_INTERVAL_MS = 2600

/**
 * Owns the generate request lifecycle: loading (with rotating status lines), success, error and
 * cancellation. Backend failures are surfaced verbatim — never replaced with invented data.
 */
export function useRecipeGeneration(): UseRecipeGeneration {
  const [state, setState] = useState<GenerationState>({
    status: 'idle',
    data: null,
    error: null,
    messageIndex: 0,
  })

  const controllerRef = useRef<AbortController | null>(null)
  const lastBodyRef = useRef<GenerateRequest | null>(null)

  const cancel = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    setState({ status: 'idle', data: null, error: null, messageIndex: 0 })
  }, [])

  const reset = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    setState({ status: 'idle', data: null, error: null, messageIndex: 0 })
  }, [])

  const start = useCallback((body: GenerateRequest) => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    lastBodyRef.current = body
    setState({ status: 'loading', data: null, error: null, messageIndex: 0 })

    generateRecipe(body, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return
        setState({ status: 'success', data, error: null, messageIndex: 0 })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        if (err instanceof ApiError) {
          setState({ status: 'error', data: null, error: err.detail, messageIndex: 0 })
          return
        }
        if (err instanceof DOMException && err.name === 'AbortError') return
        setState({
          status: 'error',
          data: null,
          error: err instanceof Error ? err.message : 'Something went wrong in the kitchen.',
          messageIndex: 0,
        })
      })
  }, [])

  const retry = useCallback(() => {
    if (lastBodyRef.current) start(lastBodyRef.current)
  }, [start])

  // Rotate the status line while a request is in flight.
  useEffect(() => {
    if (state.status !== 'loading') return
    const id = window.setInterval(() => {
      setState((prev) =>
        prev.status === 'loading'
          ? { ...prev, messageIndex: (prev.messageIndex + 1) % LOADING_MESSAGES.length }
          : prev,
      )
    }, MESSAGE_INTERVAL_MS)
    return () => window.clearInterval(id)
  }, [state.status])

  useEffect(() => () => controllerRef.current?.abort(), [])

  return { ...state, start, cancel, retry, reset }
}
