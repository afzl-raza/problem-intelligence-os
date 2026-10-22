from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ingestion_run import IngestionStatus, IngestionType
from app.repositories.ingestion_run import IngestionRunRepository
from app.schemas.ingestion import (
    APIIngestionRequest,
    IngestionPaginatedResponse,
    IngestionRunResponse,
    RSSIngestionRequest,
    WebIngestionRequest,
)
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post(
    "/rss",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger RSS/Atom Feed Ingestion Run",
)
def trigger_rss_ingestion(
    req: RSSIngestionRequest,
    db: Session = Depends(get_db),
):
    """Fetch, parse, deduplicate, and store evidence items from an RSS/Atom XML feed."""
    return IngestionService.run_rss_ingestion(db=db, req=req)


@router.post(
    "/web",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger Web HTML Page Ingestion Run",
)
def trigger_web_ingestion(
    req: WebIngestionRequest,
    db: Session = Depends(get_db),
):
    """Fetch, parse, deduplicate, and store evidence items from a Web HTML document."""
    return IngestionService.run_web_ingestion(db=db, req=req)


@router.post(
    "/api",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger JSON REST API Ingestion Run",
)
def trigger_api_ingestion(
    req: APIIngestionRequest,
    db: Session = Depends(get_db),
):
    """Fetch, parse, deduplicate, and store evidence items from a structured JSON feed."""
    return IngestionService.run_api_ingestion(db=db, req=req)


@router.get(
    "/runs",
    response_model=IngestionPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List Ingestion Job Runs with Pagination & Filtering",
)
def list_ingestion_runs(
    source_id: UUID | None = Query(None, description="Filter runs by data source UUID"),
    status: IngestionStatus | None = Query(None, description="Filter runs by execution status"),
    ingestion_type: IngestionType | None = Query(None, description="Filter runs by ingestion type"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit per page"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated ingestion job runs with optional filtering criteria."""
    items, total = IngestionRunRepository.list(
        db=db,
        source_id=source_id,
        status=status,
        ingestion_type=ingestion_type,
        skip=skip,
        limit=limit,
    )
    return IngestionPaginatedResponse(
        items=[IngestionRunResponse.model_validate(run) for run in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/runs/{run_id}",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Ingestion Job Run Details",
)
def get_ingestion_run(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve detailed execution status and metrics for a specific ingestion run."""
    run = IngestionRunRepository.get_by_id(db=db, run_id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IngestionRun with id '{run_id}' not found.",
        )
    return run
