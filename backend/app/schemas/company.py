from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.company import FundingStage


class CompanyCreate(BaseModel):
    name: str
    legal_name: str | None = None
    description: str | None = None
    website_url: str | None = None
    linkedin_url: str | None = None
    problem_summary: str | None = None
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    founded_year: int | None = None
    funding_stage: FundingStage = FundingStage.UNKNOWN
    contact_email: str | None = None
    contact_phone: str | None = None
    source: str | None = None
    source_url: str | None = None


class CompanyResponse(CompanyCreate):
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class CompanyUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    description: str | None = None
    website_url: str | None = None
    linkedin_url: str | None = None
    problem_summary: str | None = None
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    founded_year: int | None = None
    funding_stage: FundingStage | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    source: str | None = None
    source_url: str | None = None


class CompanyPaginatedResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
    skip: int
    limit: int


class CompanySearchMatch(CompanyResponse):
    relevance_score: float


class CompanySearchResponse(BaseModel):
    items: list[CompanySearchMatch]
    total: int
    skip: int
    limit: int


class CompanyMatch(BaseModel):
    id: UUID
    name: str
    similarity_score: float
    is_exact_match: bool


class CompanyMergeRequest(BaseModel):
    keep_company_id: UUID
    duplicate_company_id: UUID


class CompanyMergeResponse(BaseModel):
    company: CompanyResponse
    merged_company_id: UUID