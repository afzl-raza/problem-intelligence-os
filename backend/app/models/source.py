from enum import Enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SourceType(str, Enum):
    COMPANY_WEBSITE = "company_website"
    NEWS_ARTICLE = "news_article"
    ACADEMIC_PAPER = "academic_paper"
    CODE_REPOSITORY = "code_repository"
    REGULATORY_FILING = "regulatory_filing"
    STARTUP_DATABASE = "startup_database"
    SOCIAL_MEDIA = "social_media"
    JOB_POSTING = "job_posting"
    MANUAL_ENTRY = "manual_entry"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType),
        nullable=False,
        default=SourceType.MANUAL_ENTRY,
        index=True,
    )

    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
