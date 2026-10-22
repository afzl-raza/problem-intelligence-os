import type { FetchState } from '../api/fetchState'
import type { ProblemMatch, ProblemSearchResponse } from '../api/types'

interface ProblemResultsProps {
  state: FetchState<ProblemSearchResponse>
  selectedProblemId: string | null
  onSelect: (problem: ProblemMatch) => void
}

export function ProblemResults({ state, selectedProblemId, onSelect }: ProblemResultsProps) {
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
    return <p className="hint">No problems matched that search. Try different wording.</p>
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
            {problem.description && <p className="card__body">{problem.description}</p>}
            <div className="card__meta">
              {problem.category && <span>{problem.category}</span>}
              <span>relevance {problem.relevance_score.toFixed(2)}</span>
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}
