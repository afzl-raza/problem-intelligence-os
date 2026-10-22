from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.evidence import ConfidenceLevel, EvidenceRecord, EvidenceType
from app.schemas.evidence import EvidenceCreate, EvidenceUpdate


def create_evidence(
    db: Session,
    evidence_data: EvidenceCreate,
) -> EvidenceRecord:
    data = evidence_data.model_dump()
    if data.get("retrieved_at") is None:
        data["retrieved_at"] = datetime.now(timezone.utc)

    evidence = EvidenceRecord(**data)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


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
) -> tuple[list[EvidenceRecord], int]:
    statement = select(EvidenceRecord)

    if company_id:
        statement = statement.where(EvidenceRecord.company_id == company_id)
    if problem_id:
        statement = statement.where(EvidenceRecord.problem_id == problem_id)
    if source_id:
        statement = statement.where(EvidenceRecord.source_id == source_id)
    if evidence_type:
        statement = statement.where(EvidenceRecord.evidence_type == evidence_type)
    if confidence_score:
        statement = statement.where(EvidenceRecord.confidence_score == confidence_score)
    if content_hash:
        statement = statement.where(EvidenceRecord.content_hash == content_hash)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.scalar(count_statement) or 0

    paginated_statement = (
        statement.order_by(EvidenceRecord.created_at.desc(), EvidenceRecord.id.desc())
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(paginated_statement).all())
    return items, total


def get_evidence(
    db: Session,
    evidence_id: UUID,
) -> EvidenceRecord | None:
    statement = select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
    return db.scalar(statement)


def update_evidence(
    db: Session,
    evidence: EvidenceRecord,
    evidence_data: EvidenceUpdate,
) -> EvidenceRecord:
    update_data = evidence_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(evidence, field, value)

    db.commit()
    db.refresh(evidence)
    return evidence


def delete_evidence(
    db: Session,
    evidence: EvidenceRecord,
) -> None:
    db.delete(evidence)
    db.commit()


def get_evidence_for_company_problem(
    db: Session,
    company_id: UUID,
    problem_id: UUID,
) -> list[EvidenceRecord]:
    statement = (
        select(EvidenceRecord)
        .where(
            EvidenceRecord.company_id == company_id,
            EvidenceRecord.problem_id == problem_id,
        )
        .order_by(EvidenceRecord.created_at.desc(), EvidenceRecord.id.desc())
    )
    return list(db.scalars(statement).all())
