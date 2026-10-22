from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import NO_NUL_PATTERN
from app.db.session import get_db
from app.models.problem import ImpactLevel
from app.schemas.landscape import DomainLandscape
from app.services.landscape import get_domain_landscape
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


@router.get(
    "/{slug}/landscape",
    response_model=DomainLandscape,
    summary="Domain landscape",
    description=(
        "Everything the domain page needs in one call: counts, category / impact / "
        "funding distributions, the companies linked through the domain's problems, "
        "and a paginated, filterable problem list with company and evidence counts. "
        "Counts are raw numbers about PIOS's dataset, not market conclusions."
    ),
)
def get_domain_landscape_endpoint(
    slug: str,
    category: str | None = Query(None, min_length=1, pattern=NO_NUL_PATTERN, description="Filter problems by exact category"),
    impact_level: ImpactLevel | None = Query(None, description="Filter problems by impact level"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    landscape = get_domain_landscape(db, slug, category=category, impact_level=impact_level, skip=skip, limit=limit)
    if landscape is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )
    return landscape
