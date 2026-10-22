from collections import defaultdict
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_problem import CompanyProblem
from app.models.domain import ProblemDomain
from app.models.evidence import EvidenceRecord
from app.models.problem import ImpactLevel, Problem
from app.models.source import Source
from app.repositories.domain import get_domain_with_counts


def get_domain_landscape(
    db: Session,
    slug: str,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict | None:
    """Everything the domain page needs. Domain counts come from the same
    function as GET /domains, so the two can never disagree."""
    counted = get_domain_with_counts(db, slug)
    if counted is None:
        return None
    domain, problem_count, company_count = counted

    in_domain = Problem.id.in_(select(ProblemDomain.problem_id).where(ProblemDomain.domain_id == domain.id))

    categories = db.execute(
        select(Problem.category, func.count(Problem.id))
        .where(in_domain, Problem.category.isnot(None))
        .group_by(Problem.category)
        .order_by(func.count(Problem.id).desc(), Problem.category)
    ).all()
    impacts = db.execute(
        select(Problem.impact_level, func.count(Problem.id))
        .where(in_domain)
        .group_by(Problem.impact_level)
        .order_by(func.count(Problem.id).desc())
    ).all()

    domain_links = (
        select(CompanyProblem.company_id, CompanyProblem.problem_id)
        .join(ProblemDomain, ProblemDomain.problem_id == CompanyProblem.problem_id)
        .where(ProblemDomain.domain_id == domain.id)
        .subquery()
    )
    funding = db.execute(
        select(Company.funding_stage, func.count(distinct(Company.id)))
        .join(domain_links, domain_links.c.company_id == Company.id)
        .group_by(Company.funding_stage)
        .order_by(func.count(distinct(Company.id)).desc(), Company.funding_stage)
    ).all()
    companies = db.execute(
        select(Company, func.count(distinct(domain_links.c.problem_id)))
        .join(domain_links, domain_links.c.company_id == Company.id)
        .group_by(Company.id)
        .order_by(func.count(distinct(domain_links.c.problem_id)).desc(), Company.name)
        .limit(200)
    ).all()

    conditions = [in_domain]
    if category:
        conditions.append(func.lower(Problem.category) == category.lower())
    if impact_level:
        conditions.append(Problem.impact_level == impact_level)

    total = db.scalar(select(func.count(Problem.id)).where(*conditions)) or 0
    page = db.scalars(
        select(Problem)
        .where(*conditions)
        .order_by(Problem.title, Problem.id)
        .offset(skip)
        .limit(limit)
    ).all()

    page_ids = [p.id for p in page]
    company_counts: dict[UUID, int] = {}
    evidence_rows: dict[UUID, list] = defaultdict(list)
    if page_ids:
        company_counts = dict(
            db.execute(
                select(CompanyProblem.problem_id, func.count(distinct(CompanyProblem.company_id)))
                .where(CompanyProblem.problem_id.in_(page_ids))
                .group_by(CompanyProblem.problem_id)
            ).all()
        )
        for problem_id, confidence, source_verified in db.execute(
            select(EvidenceRecord.problem_id, EvidenceRecord.confidence_score, Source.is_verified)
            .outerjoin(Source, Source.id == EvidenceRecord.source_id)
            .where(EvidenceRecord.problem_id.in_(page_ids))
        ).all():
            evidence_rows[problem_id].append((confidence, source_verified))

    return {
        "domain": (domain, problem_count, company_count),
        "categories": [(name, count) for name, count in categories],
        "impacts": [(level, count) for level, count in impacts],
        "funding": [(stage, count) for stage, count in funding],
        "companies": [(company, int(n)) for company, n in companies],
        "problems": [
            {
                "problem": p,
                "company_count": int(company_counts.get(p.id, 0)),
                "evidence": evidence_rows[p.id],
            }
            for p in page
        ],
        "problems_total": total,
    }
