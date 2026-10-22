from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.models.source import SourceType


class SourceCreate(BaseModel):
    name: str
    source_type: SourceType = SourceType.MANUAL_ENTRY
    base_url: str | None = None
    is_verified: bool = True


class SourceUpdate(BaseModel):
    name: str | None = None
    source_type: SourceType | None = None
    base_url: str | None = None
    is_verified: bool | None = None


class SourceResponse(SourceCreate):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourcePaginatedResponse(BaseModel):
    items: list[SourceResponse]
    total: int
    skip: int
    limit: int
