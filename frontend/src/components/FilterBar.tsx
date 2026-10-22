import type {
  FacetCount,
  FundingStage,
  ImpactLevel,
  ProblemSearchFilters,
  SearchFacets,
} from '../api/types'
import { hasActiveFilters } from '../api/types'
import { FUNDING_STAGE_LABELS } from './labels'

interface FilterBarProps {
  facets: SearchFacets
  filters: ProblemSearchFilters
  onChange: (filters: ProblemSearchFilters) => void
}

function ChipGroup({
  label,
  facets,
  active,
  onToggle,
  formatLabel = (facet) => facet.label,
}: {
  label: string
  facets: FacetCount[]
  active: string | undefined
  onToggle: (value: string) => void
  formatLabel?: (facet: FacetCount) => string
}) {
  // A selected value that no longer appears in the facets (e.g. after the query changed)
  // must stay visible so the user can see and clear it.
  if (facets.length === 0 && !active) return null
  return (
    <div className="chip-group" role="group" aria-label={label}>
      <span className="chip-group__label">{label}</span>
      {facets.map((facet) => (
        <button
          key={facet.value}
          type="button"
          className={`chip ${active === facet.value ? 'chip--active' : ''}`}
          aria-pressed={active === facet.value}
          onClick={() => onToggle(facet.value)}
        >
          {formatLabel(facet)} <span className="chip__count">{facet.count}</span>
        </button>
      ))}
    </div>
  )
}

export function FilterBar({ facets, filters, onChange }: FilterBarProps) {
  function toggle<K extends keyof ProblemSearchFilters>(key: K, value: ProblemSearchFilters[K]) {
    onChange({ ...filters, [key]: filters[key] === value ? undefined : value })
  }

  return (
    <div className="filter-bar">
      <ChipGroup
        label="Domain"
        facets={facets.domains}
        active={filters.domain}
        onToggle={(value) => toggle('domain', value)}
      />
      <ChipGroup
        label="Category"
        facets={facets.categories}
        active={filters.category}
        onToggle={(value) => toggle('category', value)}
      />
      <ChipGroup
        label="Impact"
        facets={facets.impact_levels}
        active={filters.impact_level}
        onToggle={(value) => toggle('impact_level', value as ImpactLevel)}
      />
      <ChipGroup
        label="Company stage"
        facets={facets.funding_stages}
        active={filters.funding_stage}
        onToggle={(value) => toggle('funding_stage', value as FundingStage)}
        formatLabel={(facet) => FUNDING_STAGE_LABELS[facet.value as FundingStage] ?? facet.label}
      />
      {hasActiveFilters(filters) && (
        <button type="button" className="link-button" onClick={() => onChange({})}>
          Clear filters
        </button>
      )}
    </div>
  )
}
