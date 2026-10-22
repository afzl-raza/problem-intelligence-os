from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.ingestion_run import IngestionStatus, IngestionType


class RSSIngestionRequest(BaseModel):
    target_url: str = Field(..., description="Target RSS or Atom feed URL to ingest")
    company_id: UUID = Field(..., description="Target company UUID link")
    problem_id: UUID = Field(..., description="Target problem UUID link")
    source_id: UUID | None = Field(None, description="Optional cataloged data source UUID")


class WebIngestionRequest(BaseModel):
    target_url: str = Field(..., description="Target Web HTML page URL to ingest")
    company_id: UUID = Field(..., description="Target company UUID link")
    problem_id: UUID = Field(..., description="Target problem UUID link")
    source_id: UUID | None = Field(None, description="Optional cataloged data source UUID")


class APIIngestionRequest(BaseModel):
    target_url: str = Field(..., description="Target JSON REST API URL to ingest")
    company_id: UUID = Field(..., description="Target company UUID link")
    problem_id: UUID = Field(..., description="Target problem UUID link")
    source_id: UUID | None = Field(None, description="Optional cataloged data source UUID")


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID | None = None
    status: IngestionStatus
    ingestion_type: IngestionType
    items_extracted: int
    items_ingested: int
    items_skipped: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class IngestionPaginatedResponse(BaseModel):
    items: list[IngestionRunResponse]
    total: int
    skip: int
    limit: int
