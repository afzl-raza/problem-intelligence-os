import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { FetchState } from '../api/fetchState'

// Uniform loading / error / not-found handling for whole-page fetches.
export function FetchView<T>({
  state,
  what,
  children,
}: {
  state: FetchState<T>
  what: string
  children: (data: T) => ReactNode
}) {
  if (state.status === 'idle' || state.status === 'loading') {
    return <p className="hint">Loading {what}…</p>
  }
  if (state.status === 'error') {
    // 404 = no such record; 422 = the id in the URL isn't even well-formed. Both mean "doesn't exist" to a visitor.
    const notFound = state.httpStatus === 404 || state.httpStatus === 422
    return (
      <div className="notice">
        <p className="error">{notFound ? `This ${what} doesn't exist.` : `Couldn't load ${what}: ${state.message}`}</p>
        <Link to="/">Back to search</Link>
      </div>
    )
  }
  return <>{children(state.data)}</>
}
