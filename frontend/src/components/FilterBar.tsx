import type { FacetCount, ImpactLevel, ProblemSearchFilters, SearchFacets } from '../api/types'

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
}: {
  label: string
  facets: FacetCount[]
  active: string | undefined
  onToggle: (value: string) => void
}) {
  if (facets.length === 0) return null
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
          {facet.label} <span className="chip__count">{facet.count}</span>
        </button>
      ))}
    </div>
  )
}

export function FilterBar({ facets, filters, onChange }: FilterBarProps) {
  const hasFilters = Boolean(filters.domain || filters.impact_level)

  return (
    <div className="filter-bar">
      <ChipGroup
        label="Domain"
        facets={facets.domains}
        active={filters.domain}
        onToggle={(value) => onChange({ ...filters, domain: filters.domain === value ? undefined : value })}
      />
      <ChipGroup
        label="Impact"
        facets={facets.impact_levels}
        active={filters.impact_level}
        onToggle={(value) =>
          onChange({
            ...filters,
            impact_level: filters.impact_level === value ? undefined : (value as ImpactLevel),
          })
        }
      />
      {hasFilters && (
        <button type="button" className="link-button" onClick={() => onChange({})}>
          Clear filters
        </button>
      )}
    </div>
  )
}
