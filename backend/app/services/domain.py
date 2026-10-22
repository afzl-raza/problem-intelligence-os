from sqlalchemy.orm import Session

from app.models.domain import Domain
from app.repositories.domain import (
    attach_problem_to_domain as attach_problem_to_domain_repo,
    create_domain as create_domain_repo,
    get_domain_by_slug,
    get_domain_with_counts as get_domain_with_counts_repo,
    list_domains_with_counts as list_domains_with_counts_repo,
)
from app.models.problem import Problem
from app.utils.slug import slugify


def to_response_dict(domain: Domain, problem_count: int, company_count: int) -> dict:
    return {
        "id": domain.id,
        "slug": domain.slug,
        "name": domain.name,
        "description": domain.description,
        "created_at": domain.created_at,
        "problem_count": problem_count,
        "company_count": company_count,
    }


def get_or_create_domain(db: Session, name: str, description: str | None = None) -> tuple[Domain, bool]:
    slug = slugify(name)
    existing = get_domain_by_slug(db, slug)
    if existing is not None:
        return existing, False
    return create_domain_repo(db, slug=slug, name=name.strip(), description=description), True


def attach_problem_to_domain(db: Session, problem: Problem, domain: Domain) -> bool:
    return attach_problem_to_domain_repo(db, problem_id=problem.id, domain_id=domain.id)


def list_domains(db: Session) -> list[dict]:
    return [to_response_dict(*row) for row in list_domains_with_counts_repo(db)]


def get_domain(db: Session, slug: str) -> dict | None:
    row = get_domain_with_counts_repo(db, slug)
    return to_response_dict(*row) if row else None
