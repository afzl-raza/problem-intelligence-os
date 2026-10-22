import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { searchCompanies, searchProblems, spellcheck } from '../api/client'
import type {
  FundingStage,
  ImpactLevel,
  ProblemMatch,
  ProblemSearchFilters,
  Suggestion,
} from '../api/types'
import { hasActiveFilters } from '../api/types'
import { CompanyResults } from '../components/CompanyResults'
import { FilterBar } from '../components/FilterBar'
import { ProblemResults } from '../components/ProblemResults'
import { SearchBar } from '../components/SearchBar'
import { describeError, useFetch } from '../hooks/useFetch'

const PAGE_SIZE = 20

type Tab = 'problems' | 'companies'

function buildParams(q: string, tab: Tab, filters: ProblemSearchFilters): URLSearchParams {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (tab === 'companies') params.set('tab', tab)
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value)
  }
  return params
}

interface LoadedMore {
  key: string | null
  items: ProblemMatch[]
  loading: boolean
  error: string | null
}

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()

  // The URL is the single source of truth for what is being searched.
  const q = params.get('q')?.trim() ?? ''
  const tab: Tab = params.get('tab') === 'companies' ? 'companies' : 'problems'
  const filters: ProblemSearchFilters = {
    domain: params.get('domain') ?? undefined,
    category: params.get('category') ?? undefined,
    impact_level: (params.get('impact_level') as ImpactLevel | null) ?? undefined,
    funding_stage: (params.get('funding_stage') as FundingStage | null) ?? undefined,
  }
  const filtersActive = hasActiveFilters(filters)
  const filtersKey = JSON.stringify(filters)

  // Keep the input in step with the URL when it changes by back/forward navigation.
  const [draft, setDraft] = useState(q)
  const [seenQ, setSeenQ] = useState(q)
  if (q !== seenQ) {
    setSeenQ(q)
    setDraft(q)
  }

  const problemKey = q ? `problems:${q}:${filtersKey}` : null
  const problems = useFetch(problemKey, (signal) => searchProblems(q, filters, 0, PAGE_SIZE, signal))
  const companies = useFetch(q ? `companies:${q}` : null, (signal) => searchCompanies(q, 0, PAGE_SIZE, signal))

  const spellKey = problems.status === 'success' && problems.data.total === 0 && !filtersActive ? `spell:${q}` : null
  const spell = useFetch(spellKey, (signal) => spellcheck(q, signal))
  const correction = spell.status === 'success' ? spell.data.corrected : null

  const [more, setMore] = useState<LoadedMore>({ key: null, items: [], loading: false, error: null })
  const loadedMore = more.key === problemKey ? more : null
  const items = problems.status === 'success' ? [...problems.data.items, ...(loadedMore?.items ?? [])] : []

  async function loadMore() {
    if (problems.status !== 'success' || !problemKey) return
    const key = problemKey
    const already = loadedMore?.items ?? []
    setMore({ key, items: already, loading: true, error: null })
    try {
      const page = await searchProblems(q, filters, problems.data.items.length + already.length, PAGE_SIZE)
      // Ignore the response if the user moved on to a different search meanwhile.
      setMore((current) =>
        current.key === key ? { key, items: [...already, ...page.items], loading: false, error: null } : current,
      )
    } catch (error) {
      setMore((current) =>
        current.key === key ? { ...current, loading: false, error: describeError(error) } : current,
      )
    }
  }

  function search(query: string) {
    setParams(buildParams(query.trim(), tab, {}))
  }

  function pick(suggestion: Suggestion) {
    const target = { problem: 'problems', company: 'companies', domain: 'domains' }[suggestion.kind]
    navigate(`/${target}/${suggestion.value}`)
  }

  const problemCount = problems.status === 'success' ? problems.data.total : null
  const companyCount = companies.status === 'success' ? companies.data.total : null
  const canLoadMore = problems.status === 'success' && items.length < problems.data.total

  return (
    <div className="page">
      <SearchBar
        value={draft}
        onChange={setDraft}
        onSearch={search}
        onPick={pick}
        isLoading={problems.status === 'loading'}
      />

      {!q ? (
        <div className="intro">
          <p className="hint">Search a problem to see who's already working on it, and why.</p>
          <p>
            Or <Link to="/domains">browse domains</Link> to explore a market.
          </p>
        </div>
      ) : (
        <section className="panel">
          <div className="tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'problems'}
              className={`tab ${tab === 'problems' ? 'tab--active' : ''}`}
              onClick={() => setParams(buildParams(q, 'problems', filters))}
            >
              Problems{problemCount !== null && ` (${problemCount})`}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'companies'}
              className={`tab ${tab === 'companies' ? 'tab--active' : ''}`}
              onClick={() => setParams(buildParams(q, 'companies', filters))}
            >
              Companies{companyCount !== null && ` (${companyCount})`}
            </button>
          </div>

          {tab === 'problems' ? (
            <>
              {problems.status === 'success' && (
                <FilterBar
                  facets={problems.data.facets}
                  filters={filters}
                  onChange={(next) => setParams(buildParams(q, tab, next))}
                />
              )}
              <ProblemResults
                state={problems}
                items={items}
                filtersActive={filtersActive}
                correction={correction}
                onSearchCorrection={search}
              />
              {canLoadMore && (
                <div className="load-more">
                  <button type="button" onClick={loadMore} disabled={loadedMore?.loading}>
                    {loadedMore?.loading ? 'Loading…' : `Load more (${items.length} of ${problems.data.total})`}
                  </button>
                  {loadedMore?.error && <p className="error">Couldn't load more: {loadedMore.error}</p>}
                </div>
              )}
            </>
          ) : (
            <CompanyResults state={companies} />
          )}
        </section>
      )}
    </div>
  )
}
