import type { CompanyForProblem, EvidenceRecord, ProblemSearchResponse } from './types'

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

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)

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

export function searchProblems(query: string, skip = 0, limit = 20): Promise<ProblemSearchResponse> {
  const params = new URLSearchParams({ q: query, skip: String(skip), limit: String(limit) })
  return getJson<ProblemSearchResponse>(`/problems/search?${params.toString()}`)
}

export function getCompaniesForProblem(problemId: string): Promise<CompanyForProblem[]> {
  return getJson<CompanyForProblem[]>(`/problems/${problemId}/companies`)
}

export function getEvidenceForLink(problemId: string, companyId: string): Promise<EvidenceRecord[]> {
  return getJson<EvidenceRecord[]>(`/problems/${problemId}/companies/${companyId}/evidence`)
}
