from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.schemas.company import CompanyCreate, CompanyUpdate


def create_company(
    db: Session,
    company_data: CompanyCreate,
) -> Company:
    company = Company(**company_data.model_dump())

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


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