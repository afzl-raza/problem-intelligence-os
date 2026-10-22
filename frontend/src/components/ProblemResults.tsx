import type { FetchState } from '../api/fetchState'
import type { ProblemMatch, ProblemSearchResponse } from '../api/types'
import { Highlighted } from './Highlighted'

interface ProblemResultsProps {
  state: FetchState<ProblemSearchResponse>
  selectedProblemId: string | null
  filtersActive: boolean
  correction: string | null
  onSelect: (problem: ProblemMatch) => void
  onSearchCorrection: (query: string) => void
}

export function ProblemResults({
  state,
  selectedProblemId,
  filtersActive,
  correction,
  onSelect,
  onSearchCorrection,
}: ProblemResultsProps) {
  if (state.status === 'idle') {
    return <p className="hint">Search for a problem to see who's already working on it.</p>
  }

  if (state.status === 'loading') {
    return <p className="hint">Searching…</p>
  }

  if (state.status === 'error') {
    return <p className="error">Couldn't search problems: {state.message}</p>
  }

  if (state.data.items.length === 0) {
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
      {state.data.items.map((problem) => (
        <li key={problem.id}>
          <button
            type="button"
            className={`card ${problem.id === selectedProblemId ? 'card--selected' : ''}`}
            onClick={() => onSelect(problem)}
          >
            <div className="card__header">
              <h3>{problem.title}</h3>
              <span className="badge">{problem.impact_level}</span>
            </div>
            {problem.snippet && (
              <p className="card__body">
                <Highlighted text={problem.snippet} />
              </p>
            )}
            <div className="card__meta">
              {problem.domains.map((domain) => (
                <span key={domain.slug} className="tag">
                  {domain.name}
                </span>
              ))}
              {problem.category && <span>{problem.category}</span>}
              <span>relevance {problem.relevance_score.toFixed(2)}</span>
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}
