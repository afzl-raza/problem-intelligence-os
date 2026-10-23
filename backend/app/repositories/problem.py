from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.models.company_problem import CompanyProblem
from app.models.domain import Domain, ProblemDomain
from app.models.problem import ImpactLevel, Problem
from app.repositories.detail import domains_for_problems
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


def _filter_conditions(
    domain_slug: str | None,
    category: str | None,
    impact_level: ImpactLevel | None,
    funding_stage: FundingStage | None,
) -> list:
    """The user-selected filters as SQL conditions on Problem (shared by keyword and hybrid search)."""
    conditions = []
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
    return conditions


def _facets(db: Session, scope) -> dict:
    """Facet counts over the problems selected by `scope` (a SQL condition on Problem),
    always computed *before* the user's filters so every filter choice keeps its count."""
    domain_facets = db.execute(
        select(Domain.slug, Domain.name, func.count(distinct(Problem.id)))
        .join(ProblemDomain, ProblemDomain.domain_id == Domain.id)
        .join(Problem, Problem.id == ProblemDomain.problem_id)
        .where(scope)
        .group_by(Domain.slug, Domain.name)
        .order_by(func.count(distinct(Problem.id)).desc(), Domain.name)
    ).all()
    impact_facets = db.execute(
        select(Problem.impact_level, func.count(Problem.id))
        .where(scope)
        .group_by(Problem.impact_level)
        .order_by(func.count(Problem.id).desc())
    ).all()
    category_facets = db.execute(
        select(Problem.category, func.count(Problem.id))
        .where(scope, Problem.category.isnot(None))
        .group_by(Problem.category)
        .order_by(func.count(Problem.id).desc(), Problem.category)
    ).all()
    # Counts distinct problems, so a problem with several companies at the same
    # stage is counted once per stage, never once per company.
    funding_facets = db.execute(
        select(Company.funding_stage, func.count(distinct(Problem.id)))
        .join(CompanyProblem, CompanyProblem.company_id == Company.id)
        .join(Problem, Problem.id == CompanyProblem.problem_id)
        .where(scope)
        .group_by(Company.funding_stage)
        .order_by(func.count(distinct(Problem.id)).desc(), Company.funding_stage)
    ).all()
    return {
        "domains": [{"value": slug, "label": name, "count": count} for slug, name, count in domain_facets],
        "impact_levels": [{"value": level.value, "label": level.value, "count": count} for level, count in impact_facets],
        "categories": [{"value": cat, "label": cat, "count": count} for cat, count in category_facets],
        "funding_stages": [
            {"value": stage.value, "label": stage.value, "count": count} for stage, count in funding_facets
        ],
    }


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
    conditions = [text_match, *_filter_conditions(domain_slug, category, impact_level, funding_stage)]

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

    domains_by_problem = domains_for_problems(db, [row[0].id for row in rows])

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
        "facets": _facets(db, text_match),
    }


# ---- building blocks for hybrid (keyword + semantic) search -------------------------------------


def keyword_candidate_ids(db: Session, query: str, limit: int) -> list[UUID]:
    """Ids of the best keyword matches, best first (same ranking as search_problems)."""
    ts_query = func.websearch_to_tsquery("english", query)
    rank_expr = func.ts_rank(Problem.search_vector, ts_query)
    rows = db.execute(
        select(Problem.id)
        .where(Problem.search_vector.op("@@")(ts_query))
        .order_by(rank_expr.desc(), Problem.id.desc())
        .limit(limit)
    ).all()
    return [row[0] for row in rows]


def filter_problem_ids(
    db: Session,
    ids: list[UUID],
    domain_slug: str | None = None,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
    funding_stage: FundingStage | None = None,
) -> set[UUID]:
    """Which of `ids` satisfy the user's filters."""
    if not ids:
        return set()
    conditions = _filter_conditions(domain_slug, category, impact_level, funding_stage)
    rows = db.execute(select(Problem.id).where(Problem.id.in_(ids), *conditions)).all()
    return {row[0] for row in rows}


def facets_for_ids(db: Session, ids: list[UUID]) -> dict:
    return _facets(db, Problem.id.in_(ids))


def hydrate_problems(db: Session, ids: list[UUID], query: str) -> dict[UUID, dict]:
    """Problem rows plus highlighted snippets and domains for a page of ids (highlights come
    from the keyword query; a semantic-only hit simply has nothing highlighted)."""
    if not ids:
        return {}
    ts_query = func.websearch_to_tsquery("english", query)
    rows = db.execute(
        select(
            Problem,
            func.ts_headline("english", func.coalesce(Problem.description, ""), ts_query, _HEADLINE_OPTIONS),
            func.ts_headline("english", Problem.title, ts_query, _HEADLINE_OPTIONS),
        ).where(Problem.id.in_(ids))
    ).all()
    domains = domains_for_problems(db, ids)
    return {
        row[0].id: {"problem": row[0], "snippet": row[1], "title_snippet": row[2], "domains": domains[row[0].id]}
        for row in rows
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


def get_problems_by_ids(db: Session, ids: list[UUID]) -> dict[UUID, Problem]:
    if not ids:
        return {}
    return {p.id: p for p in db.scalars(select(Problem).where(Problem.id.in_(ids))).all()}
