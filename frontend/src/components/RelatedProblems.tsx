import { Link } from 'react-router-dom'
import { getRelatedProblems } from '../api/client'
import { useFetch } from '../hooks/useFetch'

export function RelatedProblems({ problemId }: { problemId: string }) {
  const state = useFetch(`related:${problemId}`, (signal) => getRelatedProblems(problemId, signal))

  // Meaning-based search being off or not indexed yet is not an error worth showing here.
  if (state.status === 'idle' || state.status === 'error') return null
  if (state.status === 'loading') return <p className="hint">Finding related problems…</p>
  if (!state.data.semantic_available) return null

  return (
    <section>
      <h2>Related by meaning</h2>
      <p className="hint">
        Problems whose text is close in meaning to this one, across all domains. Similarity is a relevance signal, not
        proof that two problems are the same.
      </p>
      {state.data.items.length === 0 ? (
        <p className="hint">No closely related problems in our data yet.</p>
      ) : (
        <ul className="card-list">
          {state.data.items.map((related) => (
            <li key={related.id} className="card">
              <div className="card__header">
                <h3>
                  <Link to={`/problems/${related.id}`}>{related.title}</Link>
                </h3>
                <span className="badge" title="Cosine similarity of meaning">
                  {related.similarity.toFixed(2)} similar
                </span>
              </div>
              <div className="card__meta">
                {related.domains.map((domain) => (
                  <Link key={domain.slug} to={`/domains/${domain.slug}`} className="tag">
                    {domain.name}
                  </Link>
                ))}
                {related.category && <span>{related.category}</span>}
                <span>{related.impact_level} impact</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
