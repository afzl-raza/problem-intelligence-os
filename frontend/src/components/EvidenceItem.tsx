import type { EvidenceDetail } from '../api/types'
import { EVIDENCE_TYPE_LABELS } from './labels'
import { VerificationBadge } from './VerificationBadge'

export function EvidenceItem({ evidence }: { evidence: EvidenceDetail }) {
  const { source } = evidence
  return (
    <li className="evidence-item">
      <div className="card__header">
        <span className="badge">{EVIDENCE_TYPE_LABELS[evidence.evidence_type]}</span>
        <VerificationBadge status={evidence.verification_status} />
      </div>
      <p className="card__body">{evidence.evidence_text}</p>
      <div className="evidence-item__source">
        {source ? (
          <span>
            Source: {source.name}
            {!source.is_verified && ' (source not verified)'}
          </span>
        ) : (
          <span>No cataloged source</span>
        )}
        {evidence.source_url && (
          <a href={evidence.source_url} target="_blank" rel="noreferrer">
            View source ↗
          </a>
        )}
      </div>
    </li>
  )
}

export function EvidenceList({ items }: { items: EvidenceDetail[] }) {
  if (items.length === 0) {
    return <p className="hint">No evidence recorded for this link yet.</p>
  }
  return (
    <ul className="evidence-list">
      {items.map((evidence) => (
        <EvidenceItem key={evidence.id} evidence={evidence} />
      ))}
    </ul>
  )
}
