import type { FetchState } from '../api/fetchState'
import type { EvidenceRecord } from '../api/types'

interface EvidencePanelProps {
  companyName: string
  state: FetchState<EvidenceRecord[]>
}

const EVIDENCE_TYPE_LABELS: Record<EvidenceRecord['evidence_type'], string> = {
  official_doc: 'Official document',
  press_release: 'Press release',
  product_page: 'Product page',
  patent_filing: 'Patent filing',
  user_review: 'User review',
  third_party_article: 'Third-party article',
  job_listing: 'Job listing',
  unspecified: 'Unspecified source',
}

export function EvidencePanel({ companyName, state }: EvidencePanelProps) {
  return (
    <div className="panel">
      <h2>Evidence for {companyName}</h2>

      {state.status === 'loading' && <p className="hint">Loading evidence…</p>}
      {state.status === 'error' && <p className="error">Couldn't load evidence: {state.message}</p>}
      {state.status === 'success' && state.data.length === 0 && (
        <p className="hint">No evidence recorded for this company/problem link yet.</p>
      )}

      {state.status === 'success' && state.data.length > 0 && (
        <ul className="evidence-list">
          {state.data.map((evidence) => (
            <li key={evidence.id} className="evidence-item">
              <div className="card__header">
                <span className="badge">{EVIDENCE_TYPE_LABELS[evidence.evidence_type]}</span>
                <span
                  className={`badge ${evidence.confidence_score === 'unverified' ? 'badge--unverified' : ''}`}
                >
                  {evidence.confidence_score === 'unverified'
                    ? 'Unverified / illustrative'
                    : `${evidence.confidence_score} confidence`}
                </span>
              </div>
              <p className="card__body">{evidence.evidence_text}</p>
              {evidence.source_url && (
                <a href={evidence.source_url} target="_blank" rel="noreferrer">
                  View source ↗
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
