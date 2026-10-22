import type { EvidenceType, FundingStage, RelationshipType } from '../api/types'

export const FUNDING_STAGE_LABELS: Record<FundingStage, string> = {
  pre_seed: 'Pre-seed',
  seed: 'Seed',
  series_a: 'Series A',
  series_b: 'Series B',
  series_c: 'Series C',
  growth: 'Growth',
  bootstrapped: 'Bootstrapped',
  unknown: 'Unknown stage',
}

export const EVIDENCE_TYPE_LABELS: Record<EvidenceType, string> = {
  official_doc: 'Official document',
  press_release: 'Press release',
  product_page: 'Product page',
  patent_filing: 'Patent filing',
  user_review: 'User review',
  third_party_article: 'Third-party article',
  job_listing: 'Job listing',
  unspecified: 'Unspecified source',
}

export const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  primary_focus: 'Primary focus',
  secondary_feature: 'Secondary feature',
  research_phase: 'Research phase',
  deprecated: 'Deprecated',
  unknown: 'Unknown relationship',
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`
}
