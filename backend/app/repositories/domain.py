from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.company_problem import CompanyProblem
from app.models.domain import Domain, ProblemDomain


def get_domain_by_slug(db: Session, slug: str) -> Domain | None:
    return db.scalar(select(Domain).where(Domain.slug == slug))


def create_domain(db: Session, slug: str, name: str, description: str | None = None) -> Domain:
    domain = Domain(slug=slug, name=name, description=description)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain


def attach_problem_to_domain(db: Session, problem_id: UUID, domain_id: UUID) -> bool:
    """Link a problem to a domain; returns False if the link already existed."""
    existing = db.get(ProblemDomain, (problem_id, domain_id))
    if existing is not None:
        return False
    db.add(ProblemDomain(problem_id=problem_id, domain_id=domain_id))
    db.commit()
    return True


def _counts_statement():
    problem_count = (
        select(func.count(ProblemDomain.problem_id))
        .where(ProblemDomain.domain_id == Domain.id)
        .correlate(Domain)
        .scalar_subquery()
    )
    company_count = (
        select(func.count(distinct(CompanyProblem.company_id)))
        .join(ProblemDomain, ProblemDomain.problem_id == CompanyProblem.problem_id)
        .where(ProblemDomain.domain_id == Domain.id)
        .correlate(Domain)
        .scalar_subquery()
    )
    return select(Domain, problem_count.label("problem_count"), company_count.label("company_count"))


def list_domains_with_counts(db: Session) -> list[tuple[Domain, int, int]]:
    rows = db.execute(_counts_statement().order_by(Domain.name.asc(), Domain.id.asc())).all()
    return [(row[0], int(row[1]), int(row[2])) for row in rows]


def get_domain_with_counts(db: Session, slug: str) -> tuple[Domain, int, int] | None:
    row = db.execute(_counts_statement().where(Domain.slug == slug)).first()
    if row is None:
        return None
    return row[0], int(row[1]), int(row[2])
