import { Link } from 'react-router-dom'
import type { FetchState } from '../api/fetchState'
import type { ProblemMatch, ProblemSearchResponse } from '../api/types'
import { Highlighted } from './Highlighted'

interface ProblemResultsProps {
  state: FetchState<ProblemSearchResponse>
  items: ProblemMatch[]
  filtersActive: boolean
  correction: string | null
  onSearchCorrection: (query: string) => void
}

export function ProblemResults({ state, items, filtersActive, correction, onSearchCorrection }: ProblemResultsProps) {
  if (state.status === 'idle') {
    return <p className="hint">Search for a problem to see who's already working on it.</p>
  }

  if (state.status === 'loading') {
    return <p className="hint">Searching…</p>
  }

  if (state.status === 'error') {
    return <p className="error">Couldn't search problems: {state.message}</p>
  }

  if (items.length === 0) {
    if (filtersActive) {
      return <p className="hint">No problems match the selected filters.</p>
    }
    return (
      <div className="hint">
        <p>No problems matched that search.</p>
        {correction && (
          <p>
            Did you mean{' '}
            <button type="button" className="link-button" onClick={() => onSearchCorrection(correction)}>
              {correction}
            </button>
            ?
          </p>
        )}
      </div>
    )
  }

  return (
    <ul className="card-list">
      {items.map((problem) => (
        <li key={problem.id} className="card">
          <div className="card__header">
            <h3>
              <Link to={`/problems/${problem.id}`}>
                <Highlighted text={problem.title_snippet} />
              </Link>
            </h3>
            <span className="badge">{problem.impact_level}</span>
          </div>
          {problem.snippet && (
            <p className="card__body">
              <Highlighted text={problem.snippet} />
            </p>
          )}
          <div className="card__meta">
            {problem.domains.map((domain) => (
              <Link key={domain.slug} to={`/domains/${domain.slug}`} className="tag">
                {domain.name}
              </Link>
            ))}
            {problem.category && <span>{problem.category}</span>}
            <span>relevance {problem.relevance_score.toFixed(2)}</span>
          </div>
        </li>
      ))}
    </ul>
  )
}
