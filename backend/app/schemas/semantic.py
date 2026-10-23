from uuid import UUID

from pydantic import BaseModel, Field

from app.models.problem import ImpactLevel
from app.schemas.problem import DomainRef


class RelatedProblem(BaseModel):
    id: UUID
    title: str
    category: str | None
    impact_level: ImpactLevel
    similarity: float = Field(
        description="Cosine similarity between the two problems' text. A relevance signal, not proof they are the same problem."
    )
    domains: list[DomainRef]


class RelatedProblemsResponse(BaseModel):
    items: list[RelatedProblem]
    semantic_available: bool = Field(
        description="False when meaning-based search is disabled or this problem has not been indexed yet."
    )
    min_similarity: float


class SemanticStatus(BaseModel):
    available: bool = Field(description="Meaning-based search can answer queries right now.")
    provider_enabled: bool
    model_name: str | None
    model_dimensions: int | None
    total_problems: int
    indexed: int
    stale: int | None = Field(
        description="Problems whose vector is missing or out of date (run scripts/embed_problems.py); null when the provider is disabled, since staleness is relative to a model."
    )
    semantic_min_similarity: float
    related_min_similarity: float
