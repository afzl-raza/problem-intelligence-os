from enum import Enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Computed, DateTime, JSON, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Single source of truth for the generated full-text search column, shared
# with the Alembic migration that creates it so the model and the DDL can
# never drift apart.
PROBLEM_SEARCH_VECTOR_EXPRESSION = (
    "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(description, '')), 'B') || "
    "setweight(to_tsvector('english', coalesce(category, '')), 'C')"
)


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    domain_tags: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    impact_level: Mapped[ImpactLevel] = mapped_column(
        SQLEnum(ImpactLevel),
        nullable=False,
        default=ImpactLevel.UNKNOWN,
        index=True,
    )

    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(PROBLEM_SEARCH_VECTOR_EXPRESSION, persisted=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
