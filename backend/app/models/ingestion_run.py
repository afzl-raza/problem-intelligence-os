from enum import Enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IngestionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionType(str, Enum):
    RSS = "rss"
    WEB_PAGE = "web_page"
    API_JSON = "api_json"
    MANUAL = "manual"


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[IngestionStatus] = mapped_column(
        SQLEnum(IngestionStatus),
        nullable=False,
        default=IngestionStatus.PENDING,
        index=True,
    )

    ingestion_type: Mapped[IngestionType] = mapped_column(
        SQLEnum(IngestionType),
        nullable=False,
        default=IngestionType.MANUAL,
        index=True,
    )

    items_extracted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    items_ingested: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    items_skipped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
