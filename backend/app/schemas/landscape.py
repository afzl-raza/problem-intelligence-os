from uuid import UUID

from pydantic import BaseModel

from app.models.company import FundingStage
from app.models.problem import ImpactLevel
from app.schemas.domain import DomainResponse


class CategoryCount(BaseModel):
    category: str
    problem_count: int


class ImpactCount(BaseModel):
    impact_level: ImpactLevel
    problem_count: int


class FundingCount(BaseModel):
    funding_stage: FundingStage
    company_count: int


class LandscapeCompany(BaseModel):
    id: UUID
    name: str
    industry: str | None
    website_url: str | None
    funding_stage: FundingStage
    problem_count: int


class LandscapeProblem(BaseModel):
    id: UUID
    title: str
    description: str | None
    category: str | None
    impact_level: ImpactLevel
    company_count: int
    evidence_count: int
    verified_evidence_count: int


class DomainLandscape(BaseModel):
    domain: DomainResponse
    categories: list[CategoryCount]
    impact_distribution: list[ImpactCount]
    funding_distribution: list[FundingCount]
    companies: list[LandscapeCompany]
    problems: list[LandscapeProblem]
    problems_total: int
    skip: int
    limit: int
