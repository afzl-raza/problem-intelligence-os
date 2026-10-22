export type ImpactLevel = 'low' | 'medium' | 'high' | 'critical' | 'unknown'

export type FundingStage =
  | 'pre_seed'
  | 'seed'
  | 'series_a'
  | 'series_b'
  | 'series_c'
  | 'growth'
  | 'bootstrapped'
  | 'unknown'

// Mirrors backend/app/schemas/problem.py::DomainRef
export interface DomainRef {
  slug: string
  name: string
}

// Mirrors backend/app/schemas/problem.py::ProblemResponse + ProblemMatch
export interface ProblemMatch {
  id: string
  title: string
  description: string | null
  category: string | null
  domain_tags: string[] | null
  impact_level: ImpactLevel
  created_at: string
  updated_at: string
  relevance_score: number
  // Description with matches wrapped in \u0002 ... \u0003 markers; plain text, never HTML.
  snippet: string
  domains: DomainRef[]
}

// Mirrors backend/app/schemas/problem.py::FacetCount / SearchFacets
export interface FacetCount {
  value: string
  label: string
  count: number
}

export interface SearchFacets {
  domains: FacetCount[]
  impact_levels: FacetCount[]
}

// Mirrors backend/app/schemas/problem.py::ProblemSearchResponse
export interface ProblemSearchResponse {
  items: ProblemMatch[]
  total: number
  skip: number
  limit: number
  facets: SearchFacets
}

export interface ProblemSearchFilters {
  domain?: string
  impact_level?: ImpactLevel
}

// Mirrors backend/app/schemas/company.py::CompanySearchMatch (CompanyResponse + relevance_score)
export interface CompanySearchMatch {
  id: string
  name: string
  legal_name: string | null
  description: string | null
  website_url: string | null
  industry: string | null
  country: string | null
  funding_stage: FundingStage
  relevance_score: number
}

// Mirrors backend/app/schemas/company.py::CompanySearchResponse
export interface CompanySearchResponse {
  items: CompanySearchMatch[]
  total: number
  skip: number
  limit: number
}

// Mirrors backend/app/schemas/search.py::Suggestion
export interface Suggestion {
  kind: 'problem' | 'company' | 'domain'
  label: string
  value: string
  score: number
}

// Mirrors backend/app/schemas/search.py::SpellcheckResponse
export interface SpellcheckResponse {
  query: string
  corrected: string | null
}

// Mirrors the plain dict shape returned by
// backend/app/repositories/problem.py::get_companies_for_problem
// (GET /problems/{problem_id}/companies has no response_model)
export interface CompanyForProblem {
  id: string
  name: string
  legal_name: string | null
  industry: string | null
  funding_stage: FundingStage
  relationship_type:
    | 'primary_focus'
    | 'secondary_feature'
    | 'research_phase'
    | 'deprecated'
    | 'unknown'
  evidence_summary: string | null
  linked_at: string
}

// Mirrors backend/app/schemas/evidence.py::EvidenceResponse
export interface EvidenceRecord {
  id: string
  company_id: string
  problem_id: string
  source_id: string | null
  source_url: string | null
  evidence_type:
    | 'official_doc'
    | 'press_release'
    | 'product_page'
    | 'patent_filing'
    | 'user_review'
    | 'third_party_article'
    | 'job_listing'
    | 'unspecified'
  evidence_text: string
  confidence_score: 'high' | 'medium' | 'low' | 'unverified'
  content_hash: string | null
  retrieved_at: string
  created_at: string
}
