import type {
  CompanyDetail,
  CompanySearchResponse,
  DomainLandscape,
  DomainSummary,
  ProblemDetail,
  ProblemSearchFilters,
  ProblemSearchResponse,
  RelatedProblemsResponse,
  SearchMode,
  SpellcheckResponse,
  Suggestion,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `Request failed with status ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { signal })

  if (!response.ok) {
    let detail: unknown
    try {
      detail = (await response.json()).detail
    } catch {
      detail = response.statusText
    }
    throw new ApiError(response.status, detail)
  }

  return response.json() as Promise<T>
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  return search.toString()
}

export function searchProblems(
  q: string,
  options: {
    filters?: ProblemSearchFilters
    mode?: SearchMode
    skip?: number
    limit?: number
    signal?: AbortSignal
  } = {},
): Promise<ProblemSearchResponse> {
  const { filters = {}, mode = 'keyword', skip = 0, limit = 20, signal } = options
  return getJson(`/problems/search?${query({ q, mode, skip, limit, ...filters })}`, signal)
}

export function searchCompanies(
  q: string,
  skip = 0,
  limit = 20,
  signal?: AbortSignal,
): Promise<CompanySearchResponse> {
  return getJson(`/companies/search?${query({ q, skip, limit })}`, signal)
}

export function suggest(q: string, signal?: AbortSignal): Promise<Suggestion[]> {
  return getJson(`/search/suggest?${query({ q, limit: 8 })}`, signal)
}

export function spellcheck(q: string, signal?: AbortSignal): Promise<SpellcheckResponse> {
  return getJson(`/search/spellcheck?${query({ q })}`, signal)
}

export function listDomains(signal?: AbortSignal): Promise<DomainSummary[]> {
  return getJson('/domains', signal)
}

export function getDomainLandscape(
  slug: string,
  filters: { category?: string; impact_level?: string } = {},
  signal?: AbortSignal,
): Promise<DomainLandscape> {
  return getJson(`/domains/${encodeURIComponent(slug)}/landscape?${query({ limit: 100, ...filters })}`, signal)
}

export function getProblemDetail(id: string, signal?: AbortSignal): Promise<ProblemDetail> {
  return getJson(`/problems/${encodeURIComponent(id)}/detail`, signal)
}

export function getCompanyDetail(id: string, signal?: AbortSignal): Promise<CompanyDetail> {
  return getJson(`/companies/${encodeURIComponent(id)}/detail`, signal)
}

export function getRelatedProblems(id: string, signal?: AbortSignal): Promise<RelatedProblemsResponse> {
  return getJson(`/problems/${encodeURIComponent(id)}/related`, signal)
}
