from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.models.company import FundingStage
from app.models.company_problem import RelationshipType
from app.models.evidence import ConfidenceLevel, EvidenceType
from app.models.problem import ImpactLevel
from app.models.source import SourceType
from app.schemas.company import CompanyResponse
from app.schemas.problem import DomainRef, ProblemResponse

VerificationStatus = Literal["verified", "unverified"]


class SourceRef(BaseModel):
    id: UUID
    name: str
    source_type: SourceType
    base_url: str | None
    is_verified: bool


class EvidenceDetail(BaseModel):
    id: UUID
    company_id: UUID
    problem_id: UUID
    source_url: str | None
    evidence_type: EvidenceType
    evidence_text: str
    confidence_score: ConfidenceLevel
    retrieved_at: datetime
    source: SourceRef | None
    verification_status: VerificationStatus


class ProblemCompanyDetail(BaseModel):
    id: UUID
    name: str
    industry: str | None
    country: str | None
    website_url: str | None
    funding_stage: FundingStage
    relationship_type: RelationshipType
    evidence_summary: str | None
    linked_at: datetime
    evidence: list[EvidenceDetail]


class ProblemDetail(ProblemResponse):
    domains: list[DomainRef]
    companies: list[ProblemCompanyDetail]


class CompanyProblemDetail(BaseModel):
    id: UUID
    title: str
    category: str | None
    impact_level: ImpactLevel
    relationship_type: RelationshipType
    evidence_summary: str | None
    linked_at: datetime
    domains: list[DomainRef]
    evidence: list[EvidenceDetail]


class CompanyDetail(CompanyResponse):
    problems: list[CompanyProblemDetail]
