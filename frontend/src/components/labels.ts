import type { FundingStage } from '../api/types'

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
