from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.source import SourceType
from app.schemas.source import (
    SourceCreate,
    SourcePaginatedResponse,
    SourceResponse,
    SourceUpdate,
)
from app.services.source import (
    create_source,
    delete_source,
    get_source,
    get_sources,
    update_source,
)

router = APIRouter(
    tags=["Sources"],
)


@router.post(
    "/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a data source",
    description="Registers a new data origin source in the intelligence catalog.",
)
def create_source_endpoint(
    source_data: SourceCreate,
    db: Session = Depends(get_db),
):
    return create_source(db=db, source_data=source_data)


@router.get(
    "/sources",
    response_model=SourcePaginatedResponse,
    summary="List data sources",
    description="Retrieve paginated data sources with optional filters for name, source type, and verification status.",
)
def list_sources_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (1 to 100)"),
    name: str | None = Query(None, min_length=1, description="Filter by source name (case-insensitive substring)"),
    source_type: SourceType | None = Query(None, description="Filter by source type enum"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db),
):
    return get_sources(
        db=db,
        skip=skip,
        limit=limit,
        name=name,
        source_type=source_type,
        is_verified=is_verified,
    )


@router.get(
    "/sources/{source_id}",
    response_model=SourceResponse,
    summary="Get source details",
    description="Retrieve catalog details of a specific data source.",
)
def get_source_endpoint(
    source_id: UUID,
    db: Session = Depends(get_db),
):
    source = get_source(db=db, source_id=source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    return source


@router.patch(
    "/sources/{source_id}",
    response_model=SourceResponse,
    summary="Update a data source",
    description="Update metadata for an existing data source.",
)
def update_source_endpoint(
    source_id: UUID,
    source_data: SourceUpdate,
    db: Session = Depends(get_db),
):
    source = get_source(db=db, source_id=source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    return update_source(db=db, source=source, source_data=source_data)


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a data source",
    description="Remove a data source catalog entry. Associated evidence records will have their source_id set to NULL.",
)
def delete_source_endpoint(
    source_id: UUID,
    db: Session = Depends(get_db),
):
    source = get_source(db=db, source_id=source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    delete_source(db=db, source=source)
