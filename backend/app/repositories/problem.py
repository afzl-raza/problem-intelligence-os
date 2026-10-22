from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.models.company_problem import CompanyProblem
from app.models.domain import Domain, ProblemDomain
from app.models.problem import ImpactLevel, Problem
from app.schemas.problem import CompanyProblemLink, ProblemCreate, ProblemUpdate

# Control-character highlight markers: they never occur in real text, and the
# frontend splits on them to render <mark> itself, so no HTML ever leaves the API.
SNIPPET_START = "\x02"
SNIPPET_STOP = "\x03"
_HEADLINE_OPTIONS = f"StartSel={SNIPPET_START}, StopSel={SNIPPET_STOP}, HighlightAll=true"


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


def count_problem_matches(db: Session, query: str) -> int:
    ts_query = func.websearch_to_tsquery("english", query)
    return db.scalar(select(func.count(Problem.id)).where(Problem.search_vector.op("@@")(ts_query))) or 0


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
    """Ranked full-text search over problems (title/description/category).

    `query` uses web-search syntax: "quoted phrases", OR, and -exclusion.
    Facet counts are computed over the text-matched set *before* filters,
    so the UI can show how many results each filter value would yield.
    """
    ts_query = func.websearch_to_tsquery("english", query)
    text_match = Problem.search_vector.op("@@")(ts_query)

    # One condition list feeds both the count and the page, so they can never disagree.
    conditions = [text_match]
    if domain_slug:
        conditions.append(
            Problem.id.in_(
                select(ProblemDomain.problem_id)
                .join(Domain, Domain.id == ProblemDomain.domain_id)
                .where(Domain.slug == domain_slug)
            )
        )
    if category:
        conditions.append(func.lower(Problem.category) == category.lower())
    if impact_level:
        conditions.append(Problem.impact_level == impact_level)
    if funding_stage:
        conditions.append(
            Problem.id.in_(
                select(CompanyProblem.problem_id)
                .join(Company, Company.id == CompanyProblem.company_id)
                .where(Company.funding_stage == funding_stage)
            )
        )

    total = db.scalar(select(func.count(Problem.id)).where(*conditions)) or 0

    rank_expr = func.ts_rank(Problem.search_vector, ts_query)
    snippet_expr = func.ts_headline(
        "english", func.coalesce(Problem.description, ""), ts_query, _HEADLINE_OPTIONS
    )
    title_snippet_expr = func.ts_headline("english", Problem.title, ts_query, _HEADLINE_OPTIONS)
    rows = db.execute(
        select(Problem, rank_expr, snippet_expr, title_snippet_expr)
        .where(*conditions)
        .order_by(rank_expr.desc(), Problem.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    problem_ids = [row[0].id for row in rows]
    domains_by_problem: dict[UUID, list[dict]] = {pid: [] for pid in problem_ids}
    if problem_ids:
        for problem_id, slug, name in db.execute(
            select(ProblemDomain.problem_id, Domain.slug, Domain.name)
            .join(Domain, Domain.id == ProblemDomain.domain_id)
            .where(ProblemDomain.problem_id.in_(problem_ids))
            .order_by(Domain.name)
        ).all():
            domains_by_problem[problem_id].append({"slug": slug, "name": name})

    domain_facets = db.execute(
        select(Domain.slug, Domain.name, func.count(distinct(Problem.id)))
        .join(ProblemDomain, ProblemDomain.domain_id == Domain.id)
        .join(Problem, Problem.id == ProblemDomain.problem_id)
        .where(text_match)
        .group_by(Domain.slug, Domain.name)
        .order_by(func.count(distinct(Problem.id)).desc(), Domain.name)
    ).all()
    impact_facets = db.execute(
        select(Problem.impact_level, func.count(Problem.id))
        .where(text_match)
        .group_by(Problem.impact_level)
        .order_by(func.count(Problem.id).desc())
    ).all()

    category_facets = db.execute(
        select(Problem.category, func.count(Problem.id))
        .where(text_match, Problem.category.isnot(None))
        .group_by(Problem.category)
        .order_by(func.count(Problem.id).desc(), Problem.category)
    ).all()
    # Counts distinct problems, so a problem with several companies at the same
    # stage is counted once per stage, never once per company.
    funding_facets = db.execute(
        select(Company.funding_stage, func.count(distinct(Problem.id)))
        .join(CompanyProblem, CompanyProblem.company_id == Company.id)
        .join(Problem, Problem.id == CompanyProblem.problem_id)
        .where(text_match)
        .group_by(Company.funding_stage)
        .order_by(func.count(distinct(Problem.id)).desc(), Company.funding_stage)
    ).all()

    return {
        "items": [
            {
                "problem": row[0],
                "score": float(row[1]),
                "snippet": row[2],
                "title_snippet": row[3],
                "domains": domains_by_problem[row[0].id],
            }
            for row in rows
        ],
        "total": total,
        "facets": {
            "domains": [{"value": slug, "label": name, "count": count} for slug, name, count in domain_facets],
            "impact_levels": [
                {"value": level.value, "label": level.value, "count": count} for level, count in impact_facets
            ],
            "categories": [{"value": cat, "label": cat, "count": count} for cat, count in category_facets],
            "funding_stages": [
                {"value": stage.value, "label": stage.value, "count": count} for stage, count in funding_facets
            ],
        },
    }


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
