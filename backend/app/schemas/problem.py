from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.company_problem import RelationshipType
from app.models.problem import ImpactLevel


class ProblemCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    domain_tags: list[str] | None = None
    impact_level: ImpactLevel = ImpactLevel.UNKNOWN


class ProblemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    domain_tags: list[str] | None = None
    impact_level: ImpactLevel | None = None


class ProblemResponse(ProblemCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProblemPaginatedResponse(BaseModel):
    items: list[ProblemResponse]
    total: int
    skip: int
    limit: int


class DomainRef(BaseModel):
    slug: str
    name: str


class ProblemMatch(ProblemResponse):
    relevance_score: float
    snippet: str = Field(
        description="Description with matched terms wrapped in \\u0002 (start) and \\u0003 (end) markers. Plain text, never HTML."
    )
    domains: list[DomainRef]


class FacetCount(BaseModel):
    value: str
    label: str
    count: int


class SearchFacets(BaseModel):
    domains: list[FacetCount]
    impact_levels: list[FacetCount]


class ProblemSearchResponse(BaseModel):
    items: list[ProblemMatch]
    total: int
    skip: int
    limit: int
    facets: SearchFacets


class CompanyProblemLink(BaseModel):
    relationship_type: RelationshipType = RelationshipType.PRIMARY_FOCUS
    evidence_summary: str | None = None


class CompanyProblemResponse(CompanyProblemLink):
    company_id: UUID
    problem_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
