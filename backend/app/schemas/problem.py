from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

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


class ProblemMatch(ProblemResponse):
    relevance_score: float


class ProblemSearchResponse(BaseModel):
    items: list[ProblemMatch]
    total: int
    skip: int
    limit: int


class CompanyProblemLink(BaseModel):
    relationship_type: RelationshipType = RelationshipType.PRIMARY_FOCUS
    evidence_summary: str | None = None


class CompanyProblemResponse(CompanyProblemLink):
    company_id: UUID
    problem_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
