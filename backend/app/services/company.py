from uuid import UUID
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.repositories.company import (
    create_company as create_company_repository,
    delete_company as delete_company_repository,
    get_companies as get_companies_repository,
    get_company as get_company_repository,
    update_company as update_company_repository,
)
from app.schemas.company import CompanyCreate, CompanyUpdate


def create_company(
    db: Session,
    company_data: CompanyCreate,
) -> Company:
    return create_company_repository(
        db=db,
        company_data=company_data,
    )


def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    name: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    funding_stage: FundingStage | None = None,
) -> dict:
    items, total = get_companies_repository(
        db=db,
        skip=skip,
        limit=limit,
        name=name,
        industry=industry,
        country=country,
        funding_stage=funding_stage,
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_company(
    db: Session,
    company_id: UUID,
) -> Company | None:
    return get_company_repository(
        db=db,
        company_id=company_id,
    )


def update_company(
    db: Session,
    company: Company,
    company_data: CompanyUpdate,
) -> Company:
    return update_company_repository(
        db=db,
        company=company,
        company_data=company_data,
    )


def delete_company(
    db: Session,
    company: Company,
) -> None:
    delete_company_repository(
        db=db,
        company=company,
    )

