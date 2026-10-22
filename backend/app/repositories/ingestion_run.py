from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType


class IngestionRunRepository:
    """Encapsulates all SQLAlchemy queries for IngestionRun execution tracking."""

    @staticmethod
    def create(
        db: Session,
        source_id: UUID | None,
        ingestion_type: IngestionType,
        status: IngestionStatus = IngestionStatus.RUNNING,
    ) -> IngestionRun:
        now = datetime.now(timezone.utc)
        run = IngestionRun(
            source_id=source_id,
            ingestion_type=ingestion_type,
            status=status,
            started_at=now,
            created_at=now,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_by_id(db: Session, run_id: UUID) -> IngestionRun | None:
        stmt = select(IngestionRun).where(IngestionRun.id == run_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list(
        db: Session,
        source_id: UUID | None = None,
        status: IngestionStatus | None = None,
        ingestion_type: IngestionType | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[IngestionRun], int]:
        stmt = select(IngestionRun)

        if source_id is not None:
            stmt = stmt.where(IngestionRun.source_id == source_id)
        if status is not None:
            stmt = stmt.where(IngestionRun.status == status)
        if ingestion_type is not None:
            stmt = stmt.where(IngestionRun.ingestion_type == ingestion_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar_one() or 0

        paginated_stmt = stmt.order_by(IngestionRun.created_at.desc(), IngestionRun.id.desc()).offset(skip).limit(limit)
        items = list(db.execute(paginated_stmt).scalars().all())

        return items, total

    @staticmethod
    def update_run_result(
        db: Session,
        run: IngestionRun,
        status: IngestionStatus,
        items_extracted: int = 0,
        items_ingested: int = 0,
        items_skipped: int = 0,
        error_message: str | None = None,
    ) -> IngestionRun:
        run.status = status
        run.items_extracted = items_extracted
        run.items_ingested = items_ingested
        run.items_skipped = items_skipped
        run.error_message = error_message
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run
