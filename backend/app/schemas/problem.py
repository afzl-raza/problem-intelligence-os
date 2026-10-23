from datetime import datetime
from uuid import UUID
from typing import Literal

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
    title_snippet: str = Field(
        description="Title with matched terms wrapped in \\u0002 (start) and \\u0003 (end) markers. Plain text, never HTML."
    )
    domains: list[DomainRef]
    match_type: Literal["keyword", "semantic", "both"] = "keyword"
    similarity: float | None = Field(
        default=None,
        description="Cosine similarity to the query for meaning-based matches (a relevance signal, not proof of equivalence); null for keyword-only matches.",
    )


class FacetCount(BaseModel):
    value: str
    label: str
    count: int


class SearchFacets(BaseModel):
    domains: list[FacetCount]
    impact_levels: list[FacetCount]
    categories: list[FacetCount]
    funding_stages: list[FacetCount]


class ProblemSearchResponse(BaseModel):
    items: list[ProblemMatch]
    total: int
    skip: int
    limit: int
    facets: SearchFacets
    mode_used: Literal["keyword", "hybrid"] = "keyword"
    semantic_note: str | None = Field(
        default=None, description="Why a hybrid request fell back to keyword results, when it did."
    )


class CompanyProblemLink(BaseModel):
    relationship_type: RelationshipType = RelationshipType.PRIMARY_FOCUS
    evidence_summary: str | None = None


class CompanyProblemResponse(CompanyProblemLink):
    company_id: UUID
    problem_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
