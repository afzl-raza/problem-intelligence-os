from uuid import UUID
from sqlalchemy.orm import Session

from app.models.evidence import ConfidenceLevel, EvidenceRecord, EvidenceType
from app.repositories.company import get_company
from app.repositories.evidence import (
    create_evidence as create_evidence_repo,
    delete_evidence as delete_evidence_repo,
    get_evidence as get_evidence_repo,
    get_evidence_for_company_problem as get_evidence_for_company_problem_repo,
    get_evidences as get_evidences_repo,
    update_evidence as update_evidence_repo,
)
from app.repositories.problem import get_problem
from app.repositories.source import get_source
from app.schemas.evidence import EvidenceCreate, EvidenceUpdate


def create_evidence(
    db: Session,
    evidence_data: EvidenceCreate,
) -> EvidenceRecord | None:
    # Ensure company and problem exist
    company = get_company(db=db, company_id=evidence_data.company_id)
    problem = get_problem(db=db, problem_id=evidence_data.problem_id)
    if not company or not problem:
        return None

    # If source_id provided, ensure source exists
    if evidence_data.source_id:
        source = get_source(db=db, source_id=evidence_data.source_id)
        if not source:
            return None

    return create_evidence_repo(db=db, evidence_data=evidence_data)


def get_evidences(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    company_id: UUID | None = None,
    problem_id: UUID | None = None,
    source_id: UUID | None = None,
    evidence_type: EvidenceType | None = None,
    confidence_score: ConfidenceLevel | None = None,
    content_hash: str | None = None,
) -> dict:
    items, total = get_evidences_repo(
        db=db,
        skip=skip,
        limit=limit,
        company_id=company_id,
        problem_id=problem_id,
        source_id=source_id,
        evidence_type=evidence_type,
        confidence_score=confidence_score,
        content_hash=content_hash,
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_evidence(
    db: Session,
    evidence_id: UUID,
) -> EvidenceRecord | None:
    return get_evidence_repo(db=db, evidence_id=evidence_id)


def update_evidence(
    db: Session,
    evidence: EvidenceRecord,
    evidence_data: EvidenceUpdate,
) -> EvidenceRecord:
    return update_evidence_repo(db=db, evidence=evidence, evidence_data=evidence_data)


def delete_evidence(
    db: Session,
    evidence: EvidenceRecord,
) -> None:
    delete_evidence_repo(db=db, evidence=evidence)


def get_evidence_for_company_problem(
    db: Session,
    company_id: UUID,
    problem_id: UUID,
) -> list[EvidenceRecord] | None:
    company = get_company(db=db, company_id=company_id)
    problem = get_problem(db=db, problem_id=problem_id)
    if not company or not problem:
        return None

    return get_evidence_for_company_problem_repo(
        db=db,
        company_id=company_id,
        problem_id=problem_id,
    )
