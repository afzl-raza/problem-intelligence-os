import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getDomainLandscape } from '../api/client'
import type { ImpactLevel } from '../api/types'
import { DistributionBars } from '../components/DistributionBars'
import { FetchView } from '../components/FetchView'
import { FUNDING_STAGE_LABELS, pluralize } from '../components/labels'
import { useFetch } from '../hooks/useFetch'

export function DomainPage() {
  const { slug = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const [draft, setDraft] = useState('')

  const category = params.get('category') ?? undefined
  const impact = (params.get('impact_level') as ImpactLevel | null) ?? undefined
  const state = useFetch(`domain:${slug}:${category ?? ''}:${impact ?? ''}`, (signal) =>
    getDomainLandscape(slug, { category, impact_level: impact }, signal),
  )

  function setFilter(name: 'category' | 'impact_level', value: string | undefined) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    setParams(next)
  }

  function searchInDomain(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const query = draft.trim()
    if (query) navigate(`/?${new URLSearchParams({ q: query, domain: slug })}`)
  }

  return (
    <div className="page">
      <FetchView state={state} what="domain">
        {(landscape) => (
          <>
            <header className="entity-header">
              <h1>{landscape.domain.name}</h1>
              <div className="card__meta">
                <span>{pluralize(landscape.domain.problem_count, 'problem')}</span>
                <span>{pluralize(landscape.domain.company_count, 'company', 'companies')}</span>
              </div>
              {landscape.domain.description && <p className="entity-header__body">{landscape.domain.description}</p>}
              <p className="hint">
                These are counts of what PIOS has researched in this domain, not a measure of the whole market.
              </p>
              <form className="inline-search" onSubmit={searchInDomain}>
                <input
                  type="text"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder={`Search within ${landscape.domain.name}`}
                  aria-label={`Search within ${landscape.domain.name}`}
                />
                <button type="submit" disabled={draft.trim().length === 0}>
                  Search
                </button>
              </form>
            </header>

            <div className="distributions">
              <DistributionBars
                title="Problem categories"
                items={landscape.categories.map((c) => ({ label: c.category, value: c.problem_count }))}
              />
              <DistributionBars
                title="Impact level"
                items={landscape.impact_distribution.map((i) => ({ label: i.impact_level, value: i.problem_count }))}
              />
              <DistributionBars
                title="Company funding stage"
                items={landscape.funding_distribution.map((f) => ({
                  label: FUNDING_STAGE_LABELS[f.funding_stage],
                  value: f.company_count,
                }))}
              />
            </div>

            <section>
              <h2>Problems</h2>
              <div className="filter-bar">
                <div className="chip-group" role="group" aria-label="Category">
                  <span className="chip-group__label">Category</span>
                  {landscape.categories.map((c) => (
                    <button
                      key={c.category}
                      type="button"
                      className={`chip ${category === c.category ? 'chip--active' : ''}`}
                      aria-pressed={category === c.category}
                      onClick={() => setFilter('category', category === c.category ? undefined : c.category)}
                    >
                      {c.category} <span className="chip__count">{c.problem_count}</span>
                    </button>
                  ))}
                </div>
                <div className="chip-group" role="group" aria-label="Impact">
                  <span className="chip-group__label">Impact</span>
                  {landscape.impact_distribution.map((i) => (
                    <button
                      key={i.impact_level}
                      type="button"
                      className={`chip ${impact === i.impact_level ? 'chip--active' : ''}`}
                      aria-pressed={impact === i.impact_level}
                      onClick={() => setFilter('impact_level', impact === i.impact_level ? undefined : i.impact_level)}
                    >
                      {i.impact_level} <span className="chip__count">{i.problem_count}</span>
                    </button>
                  ))}
                </div>
                {(category || impact) && (
                  <button type="button" className="link-button" onClick={() => setParams(new URLSearchParams())}>
                    Clear filters
                  </button>
                )}
              </div>

              {landscape.problems.length === 0 ? (
                <p className="hint">No problems match these filters.</p>
              ) : (
                <ul className="card-list">
                  {landscape.problems.map((problem) => (
                    <li key={problem.id} className="card">
                      <div className="card__header">
                        <h3>
                          <Link to={`/problems/${problem.id}`}>{problem.title}</Link>
                        </h3>
                        <span className="badge">{problem.impact_level}</span>
                      </div>
                      {problem.description && <p className="card__body">{problem.description}</p>}
                      <div className="card__meta">
                        {problem.category && <span>{problem.category}</span>}
                        <span>{pluralize(problem.company_count, 'company', 'companies')} in our data</span>
                        <span>
                          {problem.evidence_count} evidence ({problem.verified_evidence_count} verified)
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              {landscape.problems_total > landscape.problems.length && (
                <p className="hint">
                  Showing {landscape.problems.length} of {landscape.problems_total} problems.
                </p>
              )}
            </section>

            <section>
              <h2>Companies</h2>
              <ul className="card-list card-list--grid">
                {landscape.companies.map((company) => (
                  <li key={company.id} className="card">
                    <div className="card__header">
                      <h3>
                        <Link to={`/companies/${company.id}`}>{company.name}</Link>
                      </h3>
                      <span className="badge">{FUNDING_STAGE_LABELS[company.funding_stage]}</span>
                    </div>
                    <div className="card__meta">
                      {company.industry && <span>{company.industry}</span>}
                      <span>{pluralize(company.problem_count, 'problem')} here</span>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
      </FetchView>
    </div>
  )
}
