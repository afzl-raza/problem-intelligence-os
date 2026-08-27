from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import FundingStage
from app.schemas.company import (
    CompanyCreate,
    CompanyPaginatedResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.services.company import (
    create_company,
    delete_company,
    get_companies,
    get_company,
    update_company,
)

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new company",
    description="Registers a new company in the problem intelligence repository.",
)
def create_company_endpoint(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
):
    return create_company(
        db=db,
        company_data=company_data,
    )


@router.get(
    "",
    response_model=CompanyPaginatedResponse,
    summary="List companies",
    description="Retrieve paginated companies with optional filters and deterministic ordering (created_at DESC).",
)
def list_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (1 to 100)"),
    name: str | None = Query(None, min_length=1, description="Filter by company name (case-insensitive substring)"),
    industry: str | None = Query(None, min_length=1, description="Filter by industry (case-insensitive substring)"),
    country: str | None = Query(None, min_length=1, description="Filter by country (case-insensitive substring)"),
    funding_stage: FundingStage | None = Query(None, description="Filter by funding stage enum"),
    db: Session = Depends(get_db),
):
    return get_companies(
        db=db,
        skip=skip,
        limit=limit,
        name=name,
        industry=industry,
        country=country,
        funding_stage=funding_stage,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get company by ID",
    description="Retrieve a single company record by its unique UUID.",
)
def get_company_endpoint(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    company = get_company(
        db=db,
        company_id=company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Partially update company",
    description="Update specified fields of an existing company record by its UUID.",
)
def update_company_endpoint(
    company_id: UUID,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
):
    company = get_company(
        db=db,
        company_id=company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return update_company(
        db=db,
        company=company,
        company_data=company_data,
    )


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete company",
    description="Remove a company record by its unique UUID.",
)
def delete_company_endpoint(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    company = get_company(
        db=db,
        company_id=company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    delete_company(
        db=db,
        company=company,
    )