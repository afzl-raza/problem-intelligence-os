// Explicit fetch-lifecycle state so "no results yet" (success, empty data)
// is never confused with "haven't searched" (idle) or "the request failed"
// (error) — each panel renders a distinct message for each case.
export type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: T }

export const idle: FetchState<never> = { status: 'idle' }
export const loading: FetchState<never> = { status: 'loading' }

export function success<T>(data: T): FetchState<T> {
  return { status: 'success', data }
}

export function failure(message: string): FetchState<never> {
  return { status: 'error', message }
}
