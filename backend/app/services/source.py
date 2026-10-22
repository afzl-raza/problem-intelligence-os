from uuid import UUID
from sqlalchemy.orm import Session

from app.models.source import Source, SourceType
from app.repositories.source import (
    create_source as create_source_repo,
    delete_source as delete_source_repo,
    get_source as get_source_repo,
    get_sources as get_sources_repo,
    update_source as update_source_repo,
)
from app.schemas.source import SourceCreate, SourceUpdate


def create_source(
    db: Session,
    source_data: SourceCreate,
) -> Source:
    return create_source_repo(db=db, source_data=source_data)


def get_sources(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    name: str | None = None,
    source_type: SourceType | None = None,
    is_verified: bool | None = None,
) -> dict:
    items, total = get_sources_repo(
        db=db,
        skip=skip,
        limit=limit,
        name=name,
        source_type=source_type,
        is_verified=is_verified,
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_source(
    db: Session,
    source_id: UUID,
) -> Source | None:
    return get_source_repo(db=db, source_id=source_id)


def update_source(
    db: Session,
    source: Source,
    source_data: SourceUpdate,
) -> Source:
    return update_source_repo(db=db, source=source, source_data=source_data)


def delete_source(
    db: Session,
    source: Source,
) -> None:
    delete_source_repo(db=db, source=source)
