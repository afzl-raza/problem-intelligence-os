from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.utils.entity_resolution import normalize_company_name


def create_company(
    db: Session,
    company_data: CompanyCreate,
) -> Company:
    data = company_data.model_dump()
    data["normalized_name"] = normalize_company_name(data["name"])
    company = Company(**data)

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


def find_similar_companies(
    db: Session,
    name: str,
    limit: int = 10,
    min_similarity: float = 0.3,
    exclude_company_id: UUID | None = None,
) -> list[tuple[Company, float, bool]]:
    """Find companies likely to be duplicates of `name`: exact normalized-name
    matches (score 1.0) ranked first, then Postgres trigram-similarity
    matches on the raw `name` column above `min_similarity`, deduplicated by
    company id so each company appears at most once."""
    normalized = normalize_company_name(name)

    matches: list[tuple[Company, float, bool]] = []
    seen_ids: set[UUID] = set()

    exact_statement = select(Company).where(Company.normalized_name == normalized)
    if exclude_company_id is not None:
        exact_statement = exact_statement.where(Company.id != exclude_company_id)

    for company in db.scalars(exact_statement).all():
        matches.append((company, 1.0, True))
        seen_ids.add(company.id)

    similarity_expr = func.similarity(Company.name, name)
    fuzzy_statement = (
        select(Company, similarity_expr.label("score"))
        .where(similarity_expr >= min_similarity)
        .order_by(similarity_expr.desc())
    )
    if exclude_company_id is not None:
        fuzzy_statement = fuzzy_statement.where(Company.id != exclude_company_id)

    for company, score in db.execute(fuzzy_statement).all():
        if company.id in seen_ids:
            continue
        matches.append((company, float(score), False))
        seen_ids.add(company.id)

    return matches[:limit]


def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    name: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    funding_stage: FundingStage | None = None,
) -> tuple[list[Company], int]:
    statement = select(Company)

    if name:
        statement = statement.where(Company.name.ilike(f"%{name}%"))
    if industry:
        statement = statement.where(Company.industry.ilike(f"%{industry}%"))
    if country:
        statement = statement.where(Company.country.ilike(f"%{country}%"))
    if funding_stage:
        statement = statement.where(Company.funding_stage == funding_stage)

    # Calculate total count for paginated results
    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.scalar(count_statement) or 0

    # Deterministic ordering by created_at DESC with id DESC tie-breaker
    paginated_statement = (
        statement.order_by(Company.created_at.desc(), Company.id.desc())
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(paginated_statement).all())
    return items, total


def get_company(
    db: Session,
    company_id: UUID,
) -> Company | None:
    statement = select(Company).where(Company.id == company_id)

    return db.scalar(statement)


def update_company(
    db: Session,
    company: Company,
    company_data: CompanyUpdate,
) -> Company:
    update_data = company_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(company, field, value)

    if "name" in update_data:
        company.normalized_name = normalize_company_name(update_data["name"])

    company.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(company)

    return company


def delete_company(
    db: Session,
    company: Company,
) -> None:
    db.delete(company)
    db.commit()