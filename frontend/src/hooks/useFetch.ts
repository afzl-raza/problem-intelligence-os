import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { type FetchState, failure, idle, loading, success } from '../api/fetchState'

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unexpected error'
}

/**
 * Fetches whenever `key` changes; `key === null` means "nothing to fetch".
 *
 * Loading is *derived* (the stored result belongs to a different key) rather
 * than set from inside the effect, and each run aborts its predecessor, so a
 * slow earlier request can never overwrite a newer one.
 */
export function useFetch<T>(key: string | null, fetcher: (signal: AbortSignal) => Promise<T>): FetchState<T> {
  const [stored, setStored] = useState<{ key: string | null; state: FetchState<T> }>({ key: null, state: idle })

  // Callers pass inline closures; keep the latest in a ref so the effect depends only on `key`.
  const fetcherRef = useRef(fetcher)
  useEffect(() => {
    fetcherRef.current = fetcher
  })

  useEffect(() => {
    if (key === null) return
    const controller = new AbortController()
    fetcherRef
      .current(controller.signal)
      .then((data) => setStored({ key, state: success(data) }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setStored({ key, state: failure(describeError(error), error instanceof ApiError ? error.status : undefined) })
      })
    return () => controller.abort()
  }, [key])

  if (key === null) return idle
  return stored.key === key ? stored.state : loading
}
