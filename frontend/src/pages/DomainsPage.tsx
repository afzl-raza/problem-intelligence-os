import { Link } from 'react-router-dom'
import { listDomains } from '../api/client'
import { FetchView } from '../components/FetchView'
import { pluralize } from '../components/labels'
import { useFetch } from '../hooks/useFetch'

export function DomainsPage() {
  const state = useFetch('domains', (signal) => listDomains(signal))

  return (
    <div className="page">
      <h1>Domains</h1>
      <p className="hint">
        Each domain groups the problems researched in one market. Counts describe PIOS's dataset, not the whole
        market.
      </p>
      <FetchView state={state} what="domains">
        {(domains) =>
          domains.length === 0 ? (
            <p className="hint">No domains have been researched yet.</p>
          ) : (
            <ul className="card-list card-list--grid">
              {domains.map((domain) => (
                <li key={domain.slug} className="card">
                  <h3>
                    <Link to={`/domains/${domain.slug}`}>{domain.name}</Link>
                  </h3>
                  <div className="card__meta">
                    <span>{pluralize(domain.problem_count, 'problem')}</span>
                    <span>{pluralize(domain.company_count, 'company', 'companies')}</span>
                  </div>
                </li>
              ))}
            </ul>
          )
        }
      </FetchView>
    </div>
  )
}
