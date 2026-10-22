import type { FetchState } from '../api/fetchState'
import type { CompanySearchResponse } from '../api/types'
import { FUNDING_STAGE_LABELS } from './labels'

export function CompanyResults({ state }: { state: FetchState<CompanySearchResponse> }) {
  if (state.status === 'idle') return null
  if (state.status === 'loading') return <p className="hint">Searching companies…</p>
  if (state.status === 'error') return <p className="error">Couldn't search companies: {state.message}</p>
  if (state.data.items.length === 0) return <p className="hint">No companies matched that search.</p>

  return (
    <ul className="card-list">
      {state.data.items.map((company) => (
        <li key={company.id} className="card card--static">
          <div className="card__header">
            <h3>{company.name}</h3>
            <span className="badge">{FUNDING_STAGE_LABELS[company.funding_stage]}</span>
          </div>
          <div className="card__meta">
            {company.industry && <span>{company.industry}</span>}
            {company.country && <span>{company.country}</span>}
            <span>relevance {company.relevance_score.toFixed(2)}</span>
          </div>
          {company.website_url && (
            <a className="card__link" href={company.website_url} target="_blank" rel="noreferrer">
              {company.website_url.replace(/^https?:\/\//, '')} ↗
            </a>
          )}
        </li>
      ))}
    </ul>
  )
}
