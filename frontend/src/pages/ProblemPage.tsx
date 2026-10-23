import { Link, useParams } from 'react-router-dom'
import { getProblemDetail } from '../api/client'
import { EvidenceList } from '../components/EvidenceItem'
import { FetchView } from '../components/FetchView'
import { FUNDING_STAGE_LABELS, RELATIONSHIP_LABELS } from '../components/labels'
import { RelatedProblems } from '../components/RelatedProblems'
import { useFetch } from '../hooks/useFetch'

export function ProblemPage() {
  const { id = '' } = useParams()
  const state = useFetch(`problem:${id}`, (signal) => getProblemDetail(id, signal))

  return (
    <div className="page">
      <FetchView state={state} what="problem">
        {(problem) => (
          <>
            <header className="entity-header">
              <div className="card__header">
                <h1>{problem.title}</h1>
                <span className="badge">{problem.impact_level} impact</span>
              </div>
              <div className="card__meta">
                {problem.domains.map((domain) => (
                  <Link key={domain.slug} to={`/domains/${domain.slug}`} className="tag">
                    {domain.name}
                  </Link>
                ))}
                {problem.category && <span>{problem.category}</span>}
              </div>
              {problem.description && <p className="entity-header__body">{problem.description}</p>}
            </header>

            <section>
              <h2>
                Companies working on this{' '}
                <span className="hint">
                  ({problem.companies.length} in our data — not a count of the whole market)
                </span>
              </h2>
              {problem.companies.length === 0 ? (
                <p className="hint">No companies are linked to this problem in our data yet.</p>
              ) : (
                <ul className="card-list">
                  {problem.companies.map((company) => (
                    <li key={company.id} className="card card--static">
                      <div className="card__header">
                        <h3>
                          <Link to={`/companies/${company.id}`}>{company.name}</Link>
                        </h3>
                        <span className="badge">{FUNDING_STAGE_LABELS[company.funding_stage]}</span>
                      </div>
                      <div className="card__meta">
                        <span>{RELATIONSHIP_LABELS[company.relationship_type]}</span>
                        {company.industry && <span>{company.industry}</span>}
                        {company.website_url && (
                          <a href={company.website_url} target="_blank" rel="noreferrer">
                            Website ↗
                          </a>
                        )}
                      </div>
                      <EvidenceList items={company.evidence} />
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <RelatedProblems problemId={problem.id} />
          </>
        )}
      </FetchView>
    </div>
  )
}
