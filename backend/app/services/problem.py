from uuid import UUID
from sqlalchemy.orm import Session

from app.models.company import FundingStage
from app.models.company_problem import CompanyProblem
from app.models.problem import ImpactLevel, Problem
from app.repositories.company import get_company
from app.repositories.problem import (
    create_problem as create_problem_repo,
    delete_problem as delete_problem_repo,
    get_companies_for_problem as get_companies_for_problem_repo,
    get_problem as get_problem_repo,
    get_problems as get_problems_repo,
    get_problems_for_company as get_problems_for_company_repo,
    link_company_to_problem as link_company_to_problem_repo,
    search_problems as search_problems_repo,
    unlink_company_from_problem as unlink_company_from_problem_repo,
    update_problem as update_problem_repo,
)
from app.schemas.problem import CompanyProblemLink, ProblemCreate, ProblemResponse, ProblemUpdate


def create_problem(
    db: Session,
    problem_data: ProblemCreate,
) -> Problem:
    return create_problem_repo(db=db, problem_data=problem_data)


def get_problems(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    title: str | None = None,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
) -> dict:
    items, total = get_problems_repo(
        db=db,
        skip=skip,
        limit=limit,
        title=title,
        category=category,
        impact_level=impact_level,
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_problem(
    db: Session,
    problem_id: UUID,
) -> Problem | None:
    return get_problem_repo(db=db, problem_id=problem_id)


def search_problems(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 20,
    domain_slug: str | None = None,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
    funding_stage: FundingStage | None = None,
) -> dict:
    result = search_problems_repo(
        db=db,
        query=query,
        skip=skip,
        limit=limit,
        domain_slug=domain_slug,
        category=category,
        impact_level=impact_level,
        funding_stage=funding_stage,
    )
    return {
        "items": [
            {
                **ProblemResponse.model_validate(problem, from_attributes=True).model_dump(),
                "relevance_score": score,
                "snippet": snippet,
                "domains": domains,
            }
            for problem, score, snippet, domains in result["items"]
        ],
        "total": result["total"],
        "skip": skip,
        "limit": limit,
        "facets": result["facets"],
    }


def update_problem(
    db: Session,
    problem: Problem,
    problem_data: ProblemUpdate,
) -> Problem:
    return update_problem_repo(
        db=db,
        problem=problem,
        problem_data=problem_data,
    )


def delete_problem(
    db: Session,
    problem: Problem,
) -> None:
    delete_problem_repo(db=db, problem=problem)


def link_company_to_problem(
    db: Session,
    problem_id: UUID,
    company_id: UUID,
    link_data: CompanyProblemLink,
) -> CompanyProblem | None:
    # Ensure both entities exist before linking
    problem = get_problem_repo(db=db, problem_id=problem_id)
    company = get_company(db=db, company_id=company_id)

    if not problem or not company:
        return None

    return link_company_to_problem_repo(
        db=db,
        company_id=company_id,
        problem_id=problem_id,
        link_data=link_data,
    )


def unlink_company_from_problem(
    db: Session,
    problem_id: UUID,
    company_id: UUID,
) -> bool:
    return unlink_company_from_problem_repo(
        db=db,
        company_id=company_id,
        problem_id=problem_id,
    )


def get_companies_for_problem(
    db: Session,
    problem_id: UUID,
) -> list[dict] | None:
    problem = get_problem_repo(db=db, problem_id=problem_id)
    if not problem:
        return None
    return get_companies_for_problem_repo(db=db, problem_id=problem_id)


def get_problems_for_company(
    db: Session,
    company_id: UUID,
) -> list[dict] | None:
    company = get_company(db=db, company_id=company_id)
    if not company:
        return None
    return get_problems_for_company_repo(db=db, company_id=company_id)
