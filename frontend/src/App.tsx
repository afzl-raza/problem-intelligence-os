import { useRef, useState } from 'react'
import './App.css'
import {
  ApiError,
  getCompaniesForProblem,
  getEvidenceForLink,
  searchCompanies,
  searchProblems,
  spellcheck,
} from './api/client'
import { type FetchState, failure, idle, loading, success } from './api/fetchState'
import type {
  CompanyForProblem,
  CompanySearchResponse,
  EvidenceRecord,
  ProblemMatch,
  ProblemSearchFilters,
  ProblemSearchResponse,
} from './api/types'
import { SearchBar } from './components/SearchBar'
import { FilterBar } from './components/FilterBar'
import { ProblemResults } from './components/ProblemResults'
import { CompanyResults } from './components/CompanyResults'
import { CompanyList } from './components/CompanyList'
import { EvidencePanel } from './components/EvidencePanel'

type ResultsTab = 'problems' | 'companies'

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unexpected error'
}

function App() {
  const [draft, setDraft] = useState('')
  const [activeQuery, setActiveQuery] = useState<string | null>(null)
  const [filters, setFilters] = useState<ProblemSearchFilters>({})
  const [tab, setTab] = useState<ResultsTab>('problems')
  const [searchState, setSearchState] = useState<FetchState<ProblemSearchResponse>>(idle)
  const [companySearchState, setCompanySearchState] = useState<FetchState<CompanySearchResponse>>(idle)
  const [correction, setCorrection] = useState<string | null>(null)
  const [selectedProblem, setSelectedProblem] = useState<ProblemMatch | null>(null)
  const [companiesState, setCompaniesState] = useState<FetchState<CompanyForProblem[]>>(idle)
  const [selectedCompany, setSelectedCompany] = useState<CompanyForProblem | null>(null)
  const [evidenceState, setEvidenceState] = useState<FetchState<EvidenceRecord[]>>(idle)

  // Each request type keeps a counter; a response is applied only if it is
  // still the latest, so fast typing or filter clicks can't show stale results.
  const problemRequest = useRef(0)
  const companyRequest = useRef(0)
  const selectionRequest = useRef(0)

  function clearSelection() {
    selectionRequest.current++
    setSelectedProblem(null)
    setCompaniesState(idle)
    setSelectedCompany(null)
    setEvidenceState(idle)
  }

  async function runProblemSearch(query: string, activeFilters: ProblemSearchFilters) {
    const requestId = ++problemRequest.current
    setSearchState(loading)
    setCorrection(null)
    try {
      const results = await searchProblems(query, activeFilters)
      if (requestId !== problemRequest.current) return
      setSearchState(success(results))
      const unfiltered = !activeFilters.domain && !activeFilters.impact_level
      if (results.total === 0 && unfiltered) {
        const check = await spellcheck(query)
        if (requestId === problemRequest.current) setCorrection(check.corrected)
      }
    } catch (error) {
      if (requestId === problemRequest.current) setSearchState(failure(describeError(error)))
    }
  }

  async function runCompanySearch(query: string) {
    const requestId = ++companyRequest.current
    setCompanySearchState(loading)
    try {
      const results = await searchCompanies(query)
      if (requestId === companyRequest.current) setCompanySearchState(success(results))
    } catch (error) {
      if (requestId === companyRequest.current) setCompanySearchState(failure(describeError(error)))
    }
  }

  function handleSearch(query: string) {
    setDraft(query)
    setActiveQuery(query)
    setFilters({})
    clearSelection()
    void runProblemSearch(query, {})
    void runCompanySearch(query)
  }

  function handleFiltersChange(next: ProblemSearchFilters) {
    if (!activeQuery) return
    setFilters(next)
    clearSelection()
    void runProblemSearch(activeQuery, next)
  }

  async function handleSelectProblem(problem: ProblemMatch) {
    const requestId = ++selectionRequest.current
    setSelectedProblem(problem)
    setSelectedCompany(null)
    setEvidenceState(idle)
    setCompaniesState(loading)
    try {
      const companies = await getCompaniesForProblem(problem.id)
      if (requestId === selectionRequest.current) setCompaniesState(success(companies))
    } catch (error) {
      if (requestId === selectionRequest.current) setCompaniesState(failure(describeError(error)))
    }
  }

  async function handleSelectCompany(company: CompanyForProblem) {
    if (!selectedProblem) return
    const requestId = ++selectionRequest.current
    setSelectedCompany(company)
    setEvidenceState(loading)
    try {
      const evidence = await getEvidenceForLink(selectedProblem.id, company.id)
      if (requestId === selectionRequest.current) setEvidenceState(success(evidence))
    } catch (error) {
      if (requestId === selectionRequest.current) setEvidenceState(failure(describeError(error)))
    }
  }

  const problemCount = searchState.status === 'success' ? searchState.data.total : null
  const companyCount = companySearchState.status === 'success' ? companySearchState.data.total : null
  const filtersActive = Boolean(filters.domain || filters.impact_level)

  return (
    <div className="app">
      <header className="app__header">
        <h1>Problem Intelligence OS</h1>
        <p className="hint">Search a problem to see who's already working on it, and why.</p>
      </header>

      <SearchBar
        value={draft}
        onChange={setDraft}
        onSearch={handleSearch}
        isLoading={searchState.status === 'loading'}
      />

      <main className="app__panels">
        <div className="panel">
          <div className="tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'problems'}
              className={`tab ${tab === 'problems' ? 'tab--active' : ''}`}
              onClick={() => setTab('problems')}
            >
              Problems{problemCount !== null && ` (${problemCount})`}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'companies'}
              className={`tab ${tab === 'companies' ? 'tab--active' : ''}`}
              onClick={() => setTab('companies')}
            >
              Companies{companyCount !== null && ` (${companyCount})`}
            </button>
          </div>

          {tab === 'problems' ? (
            <>
              {searchState.status === 'success' && (
                <FilterBar facets={searchState.data.facets} filters={filters} onChange={handleFiltersChange} />
              )}
              <ProblemResults
                state={searchState}
                selectedProblemId={selectedProblem?.id ?? null}
                filtersActive={filtersActive}
                correction={correction}
                onSelect={handleSelectProblem}
                onSearchCorrection={handleSearch}
              />
            </>
          ) : (
            <CompanyResults state={companySearchState} />
          )}
        </div>

        {tab === 'problems' && selectedProblem && (
          <CompanyList
            problemTitle={selectedProblem.title}
            state={companiesState}
            selectedCompanyId={selectedCompany?.id ?? null}
            onSelect={handleSelectCompany}
          />
        )}

        {tab === 'problems' && selectedProblem && selectedCompany && (
          <EvidencePanel companyName={selectedCompany.name} state={evidenceState} />
        )}
      </main>
    </div>
  )
}

export default App
