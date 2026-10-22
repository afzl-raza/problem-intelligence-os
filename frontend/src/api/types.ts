// Mirrors backend/app/schemas/problem.py::ProblemResponse + ProblemMatch
export interface ProblemMatch {
  id: string
  title: string
  description: string | null
  category: string | null
  domain_tags: string[] | null
  impact_level: 'low' | 'medium' | 'high' | 'critical' | 'unknown'
  created_at: string
  updated_at: string
  relevance_score: number
}

// Mirrors backend/app/schemas/problem.py::ProblemSearchResponse
export interface ProblemSearchResponse {
  items: ProblemMatch[]
  total: number
  skip: number
  limit: number
}

// Mirrors the plain dict shape returned by
// backend/app/repositories/problem.py::get_companies_for_problem
// (GET /problems/{problem_id}/companies has no response_model)
export interface CompanyForProblem {
  id: string
  name: string
  legal_name: string | null
  industry: string | null
  funding_stage:
    | 'pre_seed'
    | 'seed'
    | 'series_a'
    | 'series_b'
    | 'series_c'
    | 'growth'
    | 'bootstrapped'
    | 'unknown'
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
