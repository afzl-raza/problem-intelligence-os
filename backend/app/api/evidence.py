from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evidence import ConfidenceLevel, EvidenceType
from app.schemas.evidence import (
    EvidenceCreate,
    EvidencePaginatedResponse,
    EvidenceResponse,
    EvidenceUpdate,
)
from app.services.evidence import (
    create_evidence,
    delete_evidence,
    get_evidence,
    get_evidence_for_company_problem,
    get_evidences,
    update_evidence,
)

router = APIRouter(
    tags=["Evidence & Provenance"],
)


@router.post(
    "/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record evidence",
    description="Registers verifiable proof supporting a company-problem association.",
)
def create_evidence_endpoint(
    evidence_data: EvidenceCreate,
    db: Session = Depends(get_db),
):
    evidence = create_evidence(db=db, evidence_data=evidence_data)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced Company, Problem, or Source not found",
        )
    return evidence


@router.get(
    "/evidence",
    response_model=EvidencePaginatedResponse,
    summary="List evidence records",
    description="Retrieve paginated evidence records with multi-criteria filters.",
)
def list_evidence_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (1 to 100)"),
    company_id: UUID | None = Query(None, description="Filter by company UUID"),
    problem_id: UUID | None = Query(None, description="Filter by problem UUID"),
    source_id: UUID | None = Query(None, description="Filter by source UUID"),
    evidence_type: EvidenceType | None = Query(None, description="Filter by evidence type enum"),
    confidence_score: ConfidenceLevel | None = Query(None, description="Filter by confidence score enum"),
    content_hash: str | None = Query(None, description="Filter by content hash"),
    db: Session = Depends(get_db),
):
    return get_evidences(
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


@router.get(
    "/evidence/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get evidence record details",
    description="Retrieve details of a specific evidence record.",
)
def get_evidence_endpoint(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db=db, evidence_id=evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found",
        )
    return evidence


@router.patch(
    "/evidence/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Update evidence record",
    description="Update metadata or content for an existing evidence record.",
)
def update_evidence_endpoint(
    evidence_id: UUID,
    evidence_data: EvidenceUpdate,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db=db, evidence_id=evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found",
        )
    return update_evidence(db=db, evidence=evidence, evidence_data=evidence_data)


@router.delete(
    "/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete evidence record",
    description="Remove an evidence record.",
)
def delete_evidence_endpoint(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db=db, evidence_id=evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence record not found",
        )
    delete_evidence(db=db, evidence=evidence)


@router.get(
    "/problems/{problem_id}/companies/{company_id}/evidence",
    response_model=list[EvidenceResponse],
    summary="Get supporting evidence for a Company-Problem link",
    description="Retrieves all verifiable evidence items explaining why a company is linked to a problem statement.",
)
def get_evidence_for_link_endpoint(
    problem_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
):
    evidence_list = get_evidence_for_company_problem(
        db=db,
        company_id=company_id,
        problem_id=problem_id,
    )
    if evidence_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company or Problem entity not found",
        )
    return evidence_list
