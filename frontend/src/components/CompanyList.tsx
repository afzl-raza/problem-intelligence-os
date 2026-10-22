import type { FetchState } from '../api/fetchState'
import type { CompanyForProblem } from '../api/types'

interface CompanyListProps {
  problemTitle: string
  state: FetchState<CompanyForProblem[]>
  selectedCompanyId: string | null
  onSelect: (company: CompanyForProblem) => void
}

const FUNDING_STAGE_LABELS: Record<CompanyForProblem['funding_stage'], string> = {
  pre_seed: 'Pre-seed',
  seed: 'Seed',
  series_a: 'Series A',
  series_b: 'Series B',
  series_c: 'Series C',
  growth: 'Growth',
  bootstrapped: 'Bootstrapped',
  unknown: 'Unknown stage',
}

const RELATIONSHIP_LABELS: Record<CompanyForProblem['relationship_type'], string> = {
  primary_focus: 'Primary focus',
  secondary_feature: 'Secondary feature',
  research_phase: 'Research phase',
  deprecated: 'Deprecated',
  unknown: 'Unknown relationship',
}

export function CompanyList({ problemTitle, state, selectedCompanyId, onSelect }: CompanyListProps) {
  return (
    <div className="panel">
      <h2>Companies attacking “{problemTitle}”</h2>

      {state.status === 'loading' && <p className="hint">Loading companies…</p>}
      {state.status === 'error' && <p className="error">Couldn't load companies: {state.message}</p>}
      {state.status === 'success' && state.data.length === 0 && (
        <p className="hint">No companies linked to this problem yet.</p>
      )}

      {state.status === 'success' && state.data.length > 0 && (
        <ul className="card-list">
          {state.data.map((company) => (
            <li key={company.id}>
              <button
                type="button"
                className={`card ${company.id === selectedCompanyId ? 'card--selected' : ''}`}
                onClick={() => onSelect(company)}
              >
                <div className="card__header">
                  <h3>{company.name}</h3>
                  <span className="badge">{FUNDING_STAGE_LABELS[company.funding_stage]}</span>
                </div>
                <div className="card__meta">
                  <span>{RELATIONSHIP_LABELS[company.relationship_type]}</span>
                  {company.industry && <span>{company.industry}</span>}
                </div>
                {company.evidence_summary && <p className="card__body">{company.evidence_summary}</p>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
