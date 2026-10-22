import type { VerificationStatus } from '../api/types'

// Renders the server's verdict only; there is deliberately no client-side rule here.
export function VerificationBadge({ status }: { status: VerificationStatus }) {
  return status === 'verified' ? (
    <span className="badge badge--verified">Verified</span>
  ) : (
    <span className="badge badge--unverified" title="Summarized from the company's own page; not independently verified">
      Unverified research
    </span>
  )
}
