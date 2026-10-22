from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.evidence import ConfidenceLevel, EvidenceType


class EvidenceCreate(BaseModel):
    company_id: UUID
    problem_id: UUID
    source_id: UUID | None = None
    source_url: str | None = None
    evidence_type: EvidenceType = EvidenceType.OFFICIAL_DOC
    evidence_text: str = Field(..., min_length=1, description="Exact raw text snippet or quote supporting the relationship")
    confidence_score: ConfidenceLevel = ConfidenceLevel.HIGH
    content_hash: str | None = Field(None, max_length=64, description="Optional SHA-256 hash for deduplication")
    retrieved_at: datetime | None = None


class EvidenceUpdate(BaseModel):
    source_id: UUID | None = None
    source_url: str | None = None
    evidence_type: EvidenceType | None = None
    evidence_text: str | None = Field(None, min_length=1)
    confidence_score: ConfidenceLevel | None = None
    content_hash: str | None = Field(None, max_length=64)
    retrieved_at: datetime | None = None


class EvidenceResponse(BaseModel):
    id: UUID
    company_id: UUID
    problem_id: UUID
    source_id: UUID | None
    source_url: str | None
    evidence_type: EvidenceType
    evidence_text: str
    confidence_score: ConfidenceLevel
    content_hash: str | None
    retrieved_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidencePaginatedResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    skip: int
    limit: int
