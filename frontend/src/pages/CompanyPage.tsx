import { Link, useParams } from 'react-router-dom'
import { getCompanyDetail } from '../api/client'
import { EvidenceList } from '../components/EvidenceItem'
import { FetchView } from '../components/FetchView'
import { FUNDING_STAGE_LABELS, RELATIONSHIP_LABELS } from '../components/labels'
import { useFetch } from '../hooks/useFetch'

export function CompanyPage() {
  const { id = '' } = useParams()
  const state = useFetch(`company:${id}`, (signal) => getCompanyDetail(id, signal))

  return (
    <div className="page">
      <FetchView state={state} what="company">
        {(company) => (
          <>
            <header className="entity-header">
              <div className="card__header">
                <h1>{company.name}</h1>
                <span className="badge">{FUNDING_STAGE_LABELS[company.funding_stage]}</span>
              </div>
              <div className="card__meta">
                {company.legal_name && <span>{company.legal_name}</span>}
                {company.industry && <span>{company.industry}</span>}
                {[company.city, company.country].filter(Boolean).length > 0 && (
                  <span>{[company.city, company.country].filter(Boolean).join(', ')}</span>
                )}
                {company.founded_year && <span>Founded {company.founded_year}</span>}
                {company.website_url && (
                  <a href={company.website_url} target="_blank" rel="noreferrer">
                    Website ↗
                  </a>
                )}
              </div>
              {company.description && <p className="entity-header__body">{company.description}</p>}
            </header>

            <section>
              <h2>
                Problems it works on <span className="hint">({company.problems.length} in our data)</span>
              </h2>
              {company.problems.length === 0 ? (
                <p className="hint">No problems are linked to this company in our data yet.</p>
              ) : (
                <ul className="card-list">
                  {company.problems.map((problem) => (
                    <li key={problem.id} className="card card--static">
                      <div className="card__header">
                        <h3>
                          <Link to={`/problems/${problem.id}`}>{problem.title}</Link>
                        </h3>
                        <span className="badge">{problem.impact_level}</span>
                      </div>
                      <div className="card__meta">
                        <span>{RELATIONSHIP_LABELS[problem.relationship_type]}</span>
                        {problem.domains.map((domain) => (
                          <Link key={domain.slug} to={`/domains/${domain.slug}`} className="tag">
                            {domain.name}
                          </Link>
                        ))}
                        {problem.category && <span>{problem.category}</span>}
                      </div>
                      <EvidenceList items={problem.evidence} />
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </FetchView>
    </div>
  )
}
