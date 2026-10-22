import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="page">
      <h1>Page not found</h1>
      <p className="hint">That address doesn't match anything here.</p>
      <Link to="/">Back to search</Link>
    </div>
  )
}
