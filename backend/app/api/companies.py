from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import NO_NUL_PATTERN, SearchQuery
from app.db.session import get_db
from app.schemas.detail import CompanyDetail
from app.services.detail import get_company_detail
from app.models.company import FundingStage
from app.schemas.company import (
    CompanyCreate,
    CompanyMatch,
    CompanyMergeRequest,
    CompanyMergeResponse,
    CompanyPaginatedResponse,
    CompanyResponse,
    CompanySearchResponse,
    CompanyUpdate,
)
from app.services.company import (
    create_company,
    delete_company,
    get_companies,
    get_company,
    merge_companies,
    resolve_company_duplicates,
    search_companies,
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
    name: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by company name (case-insensitive substring)"),
    industry: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by industry (case-insensitive substring)"),
    country: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by country (case-insensitive substring)"),
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
    "/search",
    response_model=CompanySearchResponse,
    summary="Full-text search companies",
    description=(
        "Ranked full-text search over companies. A company matches on its own "
        "profile text or through any problem it is linked to. Supports "
        "\"phrases\", OR, and -exclusion."
    ),
)
def search_companies_endpoint(
    q: SearchQuery,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (1 to 100)"),
    funding_stage: FundingStage | None = Query(None, description="Filter by funding stage"),
    db: Session = Depends(get_db),
):
    return search_companies(db=db, query=q, skip=skip, limit=limit, funding_stage=funding_stage)


@router.get(
    "/resolve",
    response_model=list[CompanyMatch],
    summary="Find likely duplicate companies",
    description=(
        "Returns ranked candidate companies that may be duplicates of the given "
        "name: exact normalized-name matches first, then Postgres trigram "
        "fuzzy matches above the similarity threshold. Advisory only — never "
        "creates, blocks, or merges anything."
    ),
)
def resolve_company_duplicates_endpoint(
    name: str = Query(..., min_length=1, pattern=NO_NUL_PATTERN, description="Candidate company name to check for duplicates"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of candidate matches to return"),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0, description="Minimum trigram similarity score (0-1) for fuzzy matches"),
    db: Session = Depends(get_db),
):
    matches = resolve_company_duplicates(
        db=db,
        name=name,
        limit=limit,
        min_similarity=min_similarity,
    )
    return [
        CompanyMatch(id=company.id, name=company.name, similarity_score=score, is_exact_match=is_exact)
        for company, score, is_exact in matches
    ]


@router.post(
    "/merge",
    response_model=CompanyMergeResponse,
    summary="Merge a duplicate company into another",
    description=(
        "Reassigns evidence and problem links from `duplicate_company_id` to "
        "`keep_company_id`, then deletes the duplicate. Transactional: either "
        "fully applies or leaves both companies untouched."
    ),
)
def merge_companies_endpoint(
    merge_request: CompanyMergeRequest,
    db: Session = Depends(get_db),
):
    company = merge_companies(
        db=db,
        keep_company_id=merge_request.keep_company_id,
        duplicate_company_id=merge_request.duplicate_company_id,
    )
    return CompanyMergeResponse(
        company=CompanyResponse.model_validate(company, from_attributes=True),
        merged_company_id=merge_request.duplicate_company_id,
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

@router.get(
    "/{company_id}/detail",
    response_model=CompanyDetail,
    summary="Company detail page data",
    description=(
        "A company with every linked problem (and that problem's domains), each "
        "carrying evidence items, source records, and a server-computed "
        "verification_status."
    ),
)
def get_company_detail_endpoint(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    detail = get_company_detail(db=db, company_id=company_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return detail
