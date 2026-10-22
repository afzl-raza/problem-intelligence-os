from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import NO_NUL_PATTERN, SearchQuery
from app.db.session import get_db
from app.models.company import FundingStage
from app.models.problem import ImpactLevel
from app.schemas.problem import (
    CompanyProblemLink,
    CompanyProblemResponse,
    ProblemCreate,
    ProblemPaginatedResponse,
    ProblemResponse,
    ProblemSearchResponse,
    ProblemUpdate,
)
from app.services.problem import (
    create_problem,
    delete_problem,
    get_companies_for_problem,
    get_problem,
    get_problems,
    get_problems_for_company,
    link_company_to_problem,
    search_problems,
    unlink_company_from_problem,
    update_problem,
)

router = APIRouter(
    tags=["Problems"],
)


@router.post(
    "/problems",
    response_model=ProblemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new problem entity",
    description="Registers a new problem statement in the problem intelligence database.",
)
def create_problem_endpoint(
    problem_data: ProblemCreate,
    db: Session = Depends(get_db),
):
    return create_problem(db=db, problem_data=problem_data)


@router.get(
    "/problems",
    response_model=ProblemPaginatedResponse,
    summary="List problems",
    description="Retrieve paginated problems with optional filters and deterministic ordering (created_at DESC).",
)
def list_problems_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (1 to 100)"),
    title: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by title (case-insensitive substring)"),
    category: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by category (case-insensitive substring)"),
    impact_level: ImpactLevel | None = Query(None, description="Filter by impact level enum"),
    db: Session = Depends(get_db),
):
    return get_problems(
        db=db,
        skip=skip,
        limit=limit,
        title=title,
        category=category,
        impact_level=impact_level,
    )


@router.get(
    "/problems/search",
    response_model=ProblemSearchResponse,
    summary="Full-text search problems",
    description=(
        "Ranked full-text search over problem title/description/category. "
        "Supports web-search syntax: \"exact phrase\", OR, and -exclusion. "
        "Optional filters narrow results; facet counts are computed over the "
        "text-matched set before filtering. Additive to GET /problems."
    ),
)
def search_problems_endpoint(
    q: SearchQuery,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (1 to 100)"),
    domain: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by domain slug, e.g. parking-management-saas"),
    category: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter by exact category (case-insensitive)"),
    impact_level: ImpactLevel | None = Query(None, description="Filter by impact level"),
    funding_stage: FundingStage | None = Query(None, description="Only problems with at least one linked company at this funding stage"),
    db: Session = Depends(get_db),
):
    return search_problems(
        db=db,
        query=q,
        skip=skip,
        limit=limit,
        domain_slug=domain,
        category=category,
        impact_level=impact_level,
        funding_stage=funding_stage,
    )


@router.get(
    "/problems/{problem_id}",
    response_model=ProblemResponse,
    summary="Get problem by ID",
    description="Retrieve details of a specific problem by its UUID.",
)
def get_problem_endpoint(
    problem_id: UUID,
    db: Session = Depends(get_db),
):
    problem = get_problem(db=db, problem_id=problem_id)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )
    return problem


@router.patch(
    "/problems/{problem_id}",
    response_model=ProblemResponse,
    summary="Partially update a problem",
    description="Update specified fields of an existing problem record.",
)
def update_problem_endpoint(
    problem_id: UUID,
    problem_data: ProblemUpdate,
    db: Session = Depends(get_db),
):
    problem = get_problem(db=db, problem_id=problem_id)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )
    return update_problem(db=db, problem=problem, problem_data=problem_data)


@router.delete(
    "/problems/{problem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a problem",
    description="Remove a problem record and associated company relationship links.",
)
def delete_problem_endpoint(
    problem_id: UUID,
    db: Session = Depends(get_db),
):
    problem = get_problem(db=db, problem_id=problem_id)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )
    delete_problem(db=db, problem=problem)


# Company <-> Problem Link Endpoints

@router.post(
    "/problems/{problem_id}/companies/{company_id}",
    response_model=CompanyProblemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link a company to a problem",
    description="Establishes a relationship link between a company and a problem with metadata.",
)
def link_company_to_problem_endpoint(
    problem_id: UUID,
    company_id: UUID,
    link_data: CompanyProblemLink = CompanyProblemLink(),
    db: Session = Depends(get_db),
):
    link = link_company_to_problem(
        db=db,
        problem_id=problem_id,
        company_id=company_id,
        link_data=link_data,
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified Problem or Company was not found",
        )
    return link


@router.delete(
    "/problems/{problem_id}/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink a company from a problem",
    description="Removes the association between a company and a problem.",
)
def unlink_company_from_problem_endpoint(
    problem_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
):
    success = unlink_company_from_problem(
        db=db,
        problem_id=problem_id,
        company_id=company_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship link between company and problem not found",
        )


@router.get(
    "/problems/{problem_id}/companies",
    summary="Get companies solving a problem",
    description="Retrieve all companies attempting to solve a specific problem.",
)
def get_companies_for_problem_endpoint(
    problem_id: UUID,
    db: Session = Depends(get_db),
):
    companies = get_companies_for_problem(db=db, problem_id=problem_id)
    if companies is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )
    return companies


@router.get(
    "/companies/{company_id}/problems",
    summary="Get problems solved by a company",
    description="Retrieve all problems a specific company is actively addressing.",
)
def get_problems_for_company_endpoint(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    problems = get_problems_for_company(db=db, company_id=company_id)
    if problems is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return problems
