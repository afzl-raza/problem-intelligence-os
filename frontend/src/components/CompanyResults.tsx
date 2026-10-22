import { Link } from 'react-router-dom'
import type { FetchState } from '../api/fetchState'
import type { CompanySearchResponse } from '../api/types'
import { FUNDING_STAGE_LABELS } from './labels'

export function CompanyResults({ state }: { state: FetchState<CompanySearchResponse> }) {
  if (state.status === 'idle') return null
  if (state.status === 'loading') return <p className="hint">Searching companies…</p>
  if (state.status === 'error') return <p className="error">Couldn't search companies: {state.message}</p>
  if (state.data.items.length === 0) return <p className="hint">No companies matched that search.</p>

  return (
    <>
      <ul className="card-list">
        {state.data.items.map((company) => (
          <li key={company.id} className="card">
            <div className="card__header">
              <h3>
                <Link to={`/companies/${company.id}`}>{company.name}</Link>
              </h3>
              <span className="badge">{FUNDING_STAGE_LABELS[company.funding_stage]}</span>
            </div>
            <div className="card__meta">
              {company.industry && <span>{company.industry}</span>}
              {company.country && <span>{company.country}</span>}
              <span>relevance {company.relevance_score.toFixed(2)}</span>
            </div>
          </li>
        ))}
      </ul>
      {state.data.total > state.data.items.length && (
        <p className="hint">
          Showing {state.data.items.length} of {state.data.total} companies.
        </p>
      )}
    </>
  )
}
