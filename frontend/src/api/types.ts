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
  // Title with matches wrapped in the same markers; render it instead of `title` in result lists.
  title_snippet: string
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
  categories: FacetCount[]
  funding_stages: FacetCount[]
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
  category?: string
  funding_stage?: FundingStage
}

export function hasActiveFilters(filters: ProblemSearchFilters): boolean {
  return Object.values(filters).some(Boolean)
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

export type EvidenceType =
  | 'official_doc'
  | 'press_release'
  | 'product_page'
  | 'patent_filing'
  | 'user_review'
  | 'third_party_article'
  | 'job_listing'
  | 'unspecified'

// Mirrors backend/app/schemas/evidence.py::EvidenceResponse
export interface EvidenceRecord {
  id: string
  company_id: string
  problem_id: string
  source_id: string | null
  source_url: string | null
  evidence_type: EvidenceType
  evidence_text: string
  confidence_score: 'high' | 'medium' | 'low' | 'unverified'
  content_hash: string | null
  retrieved_at: string
  created_at: string
}

// ---- Sprint 3.3: domain, landscape, and detail pages -------------------------

export type RelationshipType =
  | 'primary_focus'
  | 'secondary_feature'
  | 'research_phase'
  | 'deprecated'
  | 'unknown'

// "verified" is decided only by the server (see backend/app/services/evidence.py);
// the UI renders it and never derives it.
export type VerificationStatus = 'verified' | 'unverified'

// Mirrors backend/app/schemas/domain.py::DomainResponse
export interface DomainSummary {
  id: string
  slug: string
  name: string
  description: string | null
  created_at: string
  problem_count: number
  company_count: number
}

// Mirrors backend/app/schemas/landscape.py
export interface CategoryCount {
  category: string
  problem_count: number
}
export interface ImpactCount {
  impact_level: ImpactLevel
  problem_count: number
}
export interface FundingCount {
  funding_stage: FundingStage
  company_count: number
}
export interface LandscapeCompany {
  id: string
  name: string
  industry: string | null
  website_url: string | null
  funding_stage: FundingStage
  problem_count: number
}
export interface LandscapeProblem {
  id: string
  title: string
  description: string | null
  category: string | null
  impact_level: ImpactLevel
  company_count: number
  evidence_count: number
  verified_evidence_count: number
}
export interface DomainLandscape {
  domain: DomainSummary
  categories: CategoryCount[]
  impact_distribution: ImpactCount[]
  funding_distribution: FundingCount[]
  companies: LandscapeCompany[]
  problems: LandscapeProblem[]
  problems_total: number
  skip: number
  limit: number
}

// Mirrors backend/app/schemas/detail.py
export interface SourceRef {
  id: string
  name: string
  source_type: string
  base_url: string | null
  is_verified: boolean
}
export interface EvidenceDetail {
  id: string
  company_id: string
  problem_id: string
  source_url: string | null
  evidence_type: EvidenceType
  evidence_text: string
  confidence_score: 'high' | 'medium' | 'low' | 'unverified'
  retrieved_at: string
  source: SourceRef | null
  verification_status: VerificationStatus
}
export interface ProblemCompanyDetail {
  id: string
  name: string
  industry: string | null
  country: string | null
  website_url: string | null
  funding_stage: FundingStage
  relationship_type: RelationshipType
  evidence_summary: string | null
  linked_at: string
  evidence: EvidenceDetail[]
}
export interface ProblemDetail {
  id: string
  title: string
  description: string | null
  category: string | null
  impact_level: ImpactLevel
  created_at: string
  updated_at: string
  domains: DomainRef[]
  companies: ProblemCompanyDetail[]
}
export interface CompanyProblemDetail {
  id: string
  title: string
  category: string | null
  impact_level: ImpactLevel
  relationship_type: RelationshipType
  evidence_summary: string | null
  linked_at: string
  domains: DomainRef[]
  evidence: EvidenceDetail[]
}
export interface CompanyDetail {
  id: string
  name: string
  legal_name: string | null
  description: string | null
  website_url: string | null
  linkedin_url: string | null
  problem_summary: string | null
  industry: string | null
  country: string | null
  city: string | null
  founded_year: number | null
  funding_stage: FundingStage
  problems: CompanyProblemDetail[]
}
