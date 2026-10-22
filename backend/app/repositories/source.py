from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.source import Source, SourceType
from app.schemas.source import SourceCreate, SourceUpdate


def create_source(
    db: Session,
    source_data: SourceCreate,
) -> Source:
    source = Source(**source_data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_sources(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    name: str | None = None,
    source_type: SourceType | None = None,
    is_verified: bool | None = None,
) -> tuple[list[Source], int]:
    statement = select(Source)

    if name:
        statement = statement.where(Source.name.ilike(f"%{name}%"))
    if source_type:
        statement = statement.where(Source.source_type == source_type)
    if is_verified is not None:
        statement = statement.where(Source.is_verified == is_verified)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.scalar(count_statement) or 0

    paginated_statement = (
        statement.order_by(Source.created_at.desc(), Source.id.desc())
        .offset(skip)
        .limit(limit)
    )

    items = list(db.scalars(paginated_statement).all())
    return items, total


def get_source(
    db: Session,
    source_id: UUID,
) -> Source | None:
    statement = select(Source).where(Source.id == source_id)
    return db.scalar(statement)


def update_source(
    db: Session,
    source: Source,
    source_data: SourceUpdate,
) -> Source:
    update_data = source_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(source, field, value)

    db.commit()
    db.refresh(source)
    return source


def delete_source(
    db: Session,
    source: Source,
) -> None:
    db.delete(source)
    db.commit()
