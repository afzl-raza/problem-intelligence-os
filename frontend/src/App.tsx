import { useState } from 'react'
import './App.css'
import { ApiError, getCompaniesForProblem, getEvidenceForLink, searchProblems } from './api/client'
import { type FetchState, failure, idle, loading, success } from './api/fetchState'
import type { CompanyForProblem, EvidenceRecord, ProblemMatch, ProblemSearchResponse } from './api/types'
import { SearchBar } from './components/SearchBar'
import { ProblemResults } from './components/ProblemResults'
import { CompanyList } from './components/CompanyList'
import { EvidencePanel } from './components/EvidencePanel'

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
  const [searchState, setSearchState] = useState<FetchState<ProblemSearchResponse>>(idle)
  const [selectedProblem, setSelectedProblem] = useState<ProblemMatch | null>(null)
  const [companiesState, setCompaniesState] = useState<FetchState<CompanyForProblem[]>>(idle)
  const [selectedCompany, setSelectedCompany] = useState<CompanyForProblem | null>(null)
  const [evidenceState, setEvidenceState] = useState<FetchState<EvidenceRecord[]>>(idle)

  async function handleSearch(query: string) {
    setSelectedProblem(null)
    setCompaniesState(idle)
    setSelectedCompany(null)
    setEvidenceState(idle)
    setSearchState(loading)
    try {
      const results = await searchProblems(query)
      setSearchState(success(results))
    } catch (error) {
      setSearchState(failure(describeError(error)))
    }
  }

  async function handleSelectProblem(problem: ProblemMatch) {
    setSelectedProblem(problem)
    setSelectedCompany(null)
    setEvidenceState(idle)
    setCompaniesState(loading)
    try {
      const companies = await getCompaniesForProblem(problem.id)
      setCompaniesState(success(companies))
    } catch (error) {
      setCompaniesState(failure(describeError(error)))
    }
  }

  async function handleSelectCompany(company: CompanyForProblem) {
    if (!selectedProblem) return
    setSelectedCompany(company)
    setEvidenceState(loading)
    try {
      const evidence = await getEvidenceForLink(selectedProblem.id, company.id)
      setEvidenceState(success(evidence))
    } catch (error) {
      setEvidenceState(failure(describeError(error)))
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1>Problem Intelligence OS</h1>
        <p className="hint">Search a problem to see who's already working on it, and why.</p>
      </header>

      <SearchBar onSearch={handleSearch} isLoading={searchState.status === 'loading'} />

      <main className="app__panels">
        <div className="panel">
          <h2>Problems</h2>
          <ProblemResults
            state={searchState}
            selectedProblemId={selectedProblem?.id ?? null}
            onSelect={handleSelectProblem}
          />
        </div>

        {selectedProblem && (
          <CompanyList
            problemTitle={selectedProblem.title}
            state={companiesState}
            selectedCompanyId={selectedCompany?.id ?? null}
            onSelect={handleSelectCompany}
          />
        )}

        {selectedProblem && selectedCompany && (
          <EvidencePanel companyName={selectedCompany.name} state={evidenceState} />
        )}
      </main>
    </div>
  )
}

export default App
