from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_problem import CompanyProblem
from app.models.problem import ImpactLevel, Problem
from app.schemas.problem import CompanyProblemLink, ProblemCreate, ProblemUpdate


def create_problem(
    db: Session,
    problem_data: ProblemCreate,
) -> Problem:
    problem = Problem(**problem_data.model_dump())
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


def get_problems(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    title: str | None = None,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
) -> tuple[list[Problem], int]:
    statement = select(Problem)

    if title:
        statement = statement.where(Problem.title.ilike(f"%{title}%"))
    if category:
        statement = statement.where(Problem.category.ilike(f"%{category}%"))
    if impact_level:
        statement = statement.where(Problem.impact_level == impact_level)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.scalar(count_statement) or 0

    paginated_statement = (
        statement.order_by(Problem.created_at.desc(), Problem.id.desc())
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(paginated_statement).all())
    return items, total


def get_problem(
    db: Session,
    problem_id: UUID,
) -> Problem | None:
    statement = select(Problem).where(Problem.id == problem_id)
    return db.scalar(statement)


def search_problems(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[tuple[Problem, float]], int]:
    """Ranked full-text search over problems using the generated
    `search_vector` tsvector column (title/description/category)."""
    ts_query = func.plainto_tsquery("english", query)
    rank_expr = func.ts_rank(Problem.search_vector, ts_query)

    base_statement = select(Problem, rank_expr.label("relevance_score")).where(
        Problem.search_vector.op("@@")(ts_query)
    )

    count_statement = select(func.count()).select_from(base_statement.subquery())
    total = db.scalar(count_statement) or 0

    paginated_statement = (
        base_statement.order_by(rank_expr.desc(), Problem.id.desc())
        .offset(skip)
        .limit(limit)
    )

    rows = db.execute(paginated_statement).all()
    items = [(row[0], float(row[1])) for row in rows]
    return items, total


def update_problem(
    db: Session,
    problem: Problem,
    problem_data: ProblemUpdate,
) -> Problem:
    update_data = problem_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(problem, field, value)

    problem.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(problem)
    return problem


def delete_problem(
    db: Session,
    problem: Problem,
) -> None:
    db.delete(problem)
    db.commit()


# Company-Problem Association Queries

def get_company_problem_link(
    db: Session,
    company_id: UUID,
    problem_id: UUID,
) -> CompanyProblem | None:
    statement = select(CompanyProblem).where(
        CompanyProblem.company_id == company_id,
        CompanyProblem.problem_id == problem_id,
    )
    return db.scalar(statement)


def link_company_to_problem(
    db: Session,
    company_id: UUID,
    problem_id: UUID,
    link_data: CompanyProblemLink,
) -> CompanyProblem:
    existing_link = get_company_problem_link(db, company_id, problem_id)

    if existing_link:
        existing_link.relationship_type = link_data.relationship_type
        existing_link.evidence_summary = link_data.evidence_summary
        db.commit()
        db.refresh(existing_link)
        return existing_link

    new_link = CompanyProblem(
        company_id=company_id,
        problem_id=problem_id,
        relationship_type=link_data.relationship_type,
        evidence_summary=link_data.evidence_summary,
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


def unlink_company_from_problem(
    db: Session,
    company_id: UUID,
    problem_id: UUID,
) -> bool:
    link = get_company_problem_link(db, company_id, problem_id)

    if link is None:
        return False

    db.delete(link)
    db.commit()
    return True


def get_companies_for_problem(
    db: Session,
    problem_id: UUID,
) -> list[dict]:
    statement = (
        select(Company, CompanyProblem)
        .join(CompanyProblem, Company.id == CompanyProblem.company_id)
        .where(CompanyProblem.problem_id == problem_id)
        .order_by(CompanyProblem.created_at.desc())
    )
    results = db.execute(statement).all()

    output = []
    for company, link in results:
        company_dict = {
            "id": company.id,
            "name": company.name,
            "legal_name": company.legal_name,
            "industry": company.industry,
            "funding_stage": company.funding_stage,
            "relationship_type": link.relationship_type,
            "evidence_summary": link.evidence_summary,
            "linked_at": link.created_at,
        }
        output.append(company_dict)

    return output


def get_problems_for_company(
    db: Session,
    company_id: UUID,
) -> list[dict]:
    statement = (
        select(Problem, CompanyProblem)
        .join(CompanyProblem, Problem.id == CompanyProblem.problem_id)
        .where(CompanyProblem.company_id == company_id)
        .order_by(CompanyProblem.created_at.desc())
    )
    results = db.execute(statement).all()

    output = []
    for problem, link in results:
        problem_dict = {
            "id": problem.id,
            "title": problem.title,
            "category": problem.category,
            "impact_level": problem.impact_level,
            "relationship_type": link.relationship_type,
            "evidence_summary": link.evidence_summary,
            "linked_at": link.created_at,
        }
        output.append(problem_dict)

    return output
