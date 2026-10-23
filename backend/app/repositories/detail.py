from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_problem import CompanyProblem
from app.models.domain import Domain, ProblemDomain
from app.models.evidence import EvidenceRecord
from app.models.problem import Problem
from app.models.source import Source


def domains_for_problems(db: Session, problem_ids: list[UUID]) -> dict[UUID, list[dict]]:
    domains: dict[UUID, list[dict]] = defaultdict(list)
    if not problem_ids:
        return domains
    rows = db.execute(
        select(ProblemDomain.problem_id, Domain.slug, Domain.name)
        .join(Domain, Domain.id == ProblemDomain.domain_id)
        .where(ProblemDomain.problem_id.in_(problem_ids))
        .order_by(Domain.name)
    ).all()
    for problem_id, slug, name in rows:
        domains[problem_id].append({"slug": slug, "name": name})
    return domains


def _evidence_with_sources(db: Session, *conditions) -> list[tuple[EvidenceRecord, Source | None]]:
    rows = db.execute(
        select(EvidenceRecord, Source)
        .outerjoin(Source, Source.id == EvidenceRecord.source_id)
        .where(*conditions)
        .order_by(EvidenceRecord.created_at.desc(), EvidenceRecord.id.desc())
    ).all()
    return [(row[0], row[1]) for row in rows]


def get_problem_detail(db: Session, problem_id: UUID) -> dict | None:
    problem = db.get(Problem, problem_id)
    if problem is None:
        return None

    links = db.execute(
        select(Company, CompanyProblem)
        .join(CompanyProblem, CompanyProblem.company_id == Company.id)
        .where(CompanyProblem.problem_id == problem_id)
        .order_by(CompanyProblem.created_at.desc(), Company.name)
    ).all()

    evidence_by_company: dict[UUID, list] = defaultdict(list)
    for evidence, source in _evidence_with_sources(db, EvidenceRecord.problem_id == problem_id):
        evidence_by_company[evidence.company_id].append((evidence, source))

    return {
        "problem": problem,
        "domains": domains_for_problems(db, [problem_id])[problem_id],
        "companies": [
            {"company": company, "link": link, "evidence": evidence_by_company[company.id]}
            for company, link in links
        ],
    }


def get_company_detail(db: Session, company_id: UUID) -> dict | None:
    company = db.get(Company, company_id)
    if company is None:
        return None

    links = db.execute(
        select(Problem, CompanyProblem)
        .join(CompanyProblem, CompanyProblem.problem_id == Problem.id)
        .where(CompanyProblem.company_id == company_id)
        .order_by(CompanyProblem.created_at.desc(), Problem.title)
    ).all()

    evidence_by_problem: dict[UUID, list] = defaultdict(list)
    for evidence, source in _evidence_with_sources(db, EvidenceRecord.company_id == company_id):
        evidence_by_problem[evidence.problem_id].append((evidence, source))

    domains = domains_for_problems(db, [problem.id for problem, _ in links])
    return {
        "company": company,
        "problems": [
            {
                "problem": problem,
                "link": link,
                "domains": domains[problem.id],
                "evidence": evidence_by_problem[problem.id],
            }
            for problem, link in links
        ],
    }
