from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.models.company_problem import CompanyProblem
from app.models.evidence import EvidenceRecord
from app.repositories.company import (
    create_company as create_company_repository,
    delete_company as delete_company_repository,
    find_similar_companies as find_similar_companies_repository,
    get_companies as get_companies_repository,
    get_company as get_company_repository,
    search_companies as search_companies_repository,
    update_company as update_company_repository,
)
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate


def search_companies(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 20,
    funding_stage: FundingStage | None = None,
) -> dict:
    items, total = search_companies_repository(
        db=db, query=query, skip=skip, limit=limit, funding_stage=funding_stage
    )
    return {
        "items": [
            {**CompanyResponse.model_validate(company, from_attributes=True).model_dump(), "relevance_score": score}
            for company, score in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def create_company(
    db: Session,
    company_data: CompanyCreate,
) -> Company:
    return create_company_repository(
        db=db,
        company_data=company_data,
    )


def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    name: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    funding_stage: FundingStage | None = None,
) -> dict:
    items, total = get_companies_repository(
        db=db,
        skip=skip,
        limit=limit,
        name=name,
        industry=industry,
        country=country,
        funding_stage=funding_stage,
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_company(
    db: Session,
    company_id: UUID,
) -> Company | None:
    return get_company_repository(
        db=db,
        company_id=company_id,
    )


def update_company(
    db: Session,
    company: Company,
    company_data: CompanyUpdate,
) -> Company:
    return update_company_repository(
        db=db,
        company=company,
        company_data=company_data,
    )


def delete_company(
    db: Session,
    company: Company,
) -> None:
    delete_company_repository(
        db=db,
        company=company,
    )


def resolve_company_duplicates(
    db: Session,
    name: str,
    limit: int = 10,
    min_similarity: float = 0.3,
) -> list[tuple[Company, float, bool]]:
    return find_similar_companies_repository(
        db=db,
        name=name,
        limit=limit,
        min_similarity=min_similarity,
    )


def merge_companies(
    db: Session,
    keep_company_id: UUID,
    duplicate_company_id: UUID,
) -> Company:
    """Merge `duplicate_company_id` into `keep_company_id`: reassign its
    evidence and problem links, then delete it. Runs as a single
    transaction so the merge can never be left half-applied."""
    if keep_company_id == duplicate_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="keep_company_id and duplicate_company_id must be different companies.",
        )

    keep_company = get_company_repository(db=db, company_id=keep_company_id)
    if keep_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id '{keep_company_id}' not found.",
        )

    duplicate_company = get_company_repository(db=db, company_id=duplicate_company_id)
    if duplicate_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id '{duplicate_company_id}' not found.",
        )

    db.execute(
        update(EvidenceRecord)
        .where(EvidenceRecord.company_id == duplicate_company_id)
        .values(company_id=keep_company_id)
    )

    duplicate_links = db.scalars(
        select(CompanyProblem).where(CompanyProblem.company_id == duplicate_company_id)
    ).all()
    for link in duplicate_links:
        existing_keep_link = db.execute(
            select(CompanyProblem).where(
                CompanyProblem.company_id == keep_company_id,
                CompanyProblem.problem_id == link.problem_id,
            )
        ).scalar_one_or_none()
        if existing_keep_link is not None:
            # Keep company already has this problem link: preserve it as-is and
            # leave the duplicate's conflicting link untouched -- it is removed
            # below by ON DELETE CASCADE when the duplicate company is deleted.
            continue
        link.company_id = keep_company_id

    db.delete(duplicate_company)
    db.commit()
    db.refresh(keep_company)

    return keep_company

