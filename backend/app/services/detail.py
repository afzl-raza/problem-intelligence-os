from uuid import UUID

from sqlalchemy.orm import Session

from app.models.evidence import EvidenceRecord
from app.models.source import Source
from app.repositories.detail import (
    get_company_detail as get_company_detail_repo,
    get_problem_detail as get_problem_detail_repo,
)
from app.schemas.company import CompanyResponse
from app.schemas.problem import ProblemResponse
from app.services.evidence import verification_status


def build_evidence_detail(evidence: EvidenceRecord, source: Source | None) -> dict:
    return {
        "id": evidence.id,
        "company_id": evidence.company_id,
        "problem_id": evidence.problem_id,
        "source_url": evidence.source_url,
        "evidence_type": evidence.evidence_type,
        "evidence_text": evidence.evidence_text,
        "confidence_score": evidence.confidence_score,
        "retrieved_at": evidence.retrieved_at,
        "source": (
            {
                "id": source.id,
                "name": source.name,
                "source_type": source.source_type,
                "base_url": source.base_url,
                "is_verified": source.is_verified,
            }
            if source is not None
            else None
        ),
        "verification_status": verification_status(evidence.confidence_score, source),
    }


def get_problem_detail(db: Session, problem_id: UUID) -> dict | None:
    detail = get_problem_detail_repo(db, problem_id)
    if detail is None:
        return None
    return {
        **ProblemResponse.model_validate(detail["problem"], from_attributes=True).model_dump(),
        "domains": detail["domains"],
        "companies": [
            {
                "id": item["company"].id,
                "name": item["company"].name,
                "industry": item["company"].industry,
                "country": item["company"].country,
                "website_url": item["company"].website_url,
                "funding_stage": item["company"].funding_stage,
                "relationship_type": item["link"].relationship_type,
                "evidence_summary": item["link"].evidence_summary,
                "linked_at": item["link"].created_at,
                "evidence": [build_evidence_detail(e, s) for e, s in item["evidence"]],
            }
            for item in detail["companies"]
        ],
    }


def get_company_detail(db: Session, company_id: UUID) -> dict | None:
    detail = get_company_detail_repo(db, company_id)
    if detail is None:
        return None
    return {
        **CompanyResponse.model_validate(detail["company"], from_attributes=True).model_dump(),
        "problems": [
            {
                "id": item["problem"].id,
                "title": item["problem"].title,
                "category": item["problem"].category,
                "impact_level": item["problem"].impact_level,
                "relationship_type": item["link"].relationship_type,
                "evidence_summary": item["link"].evidence_summary,
                "linked_at": item["link"].created_at,
                "domains": item["domains"],
                "evidence": [build_evidence_detail(e, s) for e, s in item["evidence"]],
            }
            for item in detail["problems"]
        ],
    }
