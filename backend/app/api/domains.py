from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.domain import DomainResponse
from app.services.domain import get_domain, list_domains

router = APIRouter(
    prefix="/domains",
    tags=["Domains"],
)


@router.get(
    "",
    response_model=list[DomainResponse],
    summary="List domains",
    description="All problem domains (e.g. 'Parking Management SaaS') with their problem and company counts, ordered by name.",
)
def list_domains_endpoint(db: Session = Depends(get_db)):
    return list_domains(db)


@router.get(
    "/{slug}",
    response_model=DomainResponse,
    summary="Get domain by slug",
    description="A single domain with its problem and company counts.",
)
def get_domain_endpoint(slug: str, db: Session = Depends(get_db)):
    domain = get_domain(db, slug)
    if domain is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )
    return domain
