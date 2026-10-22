import type {
  CompanyForProblem,
  CompanySearchResponse,
  EvidenceRecord,
  ProblemSearchFilters,
  ProblemSearchResponse,
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
  filters: ProblemSearchFilters = {},
  skip = 0,
  limit = 20,
): Promise<ProblemSearchResponse> {
  return getJson(`/problems/search?${query({ q, skip, limit, ...filters })}`)
}

export function searchCompanies(q: string, skip = 0, limit = 20): Promise<CompanySearchResponse> {
  return getJson(`/companies/search?${query({ q, skip, limit })}`)
}

export function suggest(q: string, signal?: AbortSignal): Promise<Suggestion[]> {
  return getJson(`/search/suggest?${query({ q, limit: 8 })}`, signal)
}

export function spellcheck(q: string): Promise<SpellcheckResponse> {
  return getJson(`/search/spellcheck?${query({ q })}`)
}

export function getCompaniesForProblem(problemId: string): Promise<CompanyForProblem[]> {
  return getJson<CompanyForProblem[]>(`/problems/${problemId}/companies`)
}

export function getEvidenceForLink(problemId: string, companyId: string): Promise<EvidenceRecord[]> {
  return getJson<EvidenceRecord[]>(`/problems/${problemId}/companies/${companyId}/evidence`)
}
