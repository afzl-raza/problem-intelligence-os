from enum import Enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RelationshipType(str, Enum):
    PRIMARY_FOCUS = "primary_focus"
    SECONDARY_FEATURE = "secondary_feature"
    RESEARCH_PHASE = "research_phase"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class CompanyProblem(Base):
    __tablename__ = "company_problems"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        primary_key=True,
    )

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    )

    relationship_type: Mapped[RelationshipType] = mapped_column(
        SQLEnum(RelationshipType),
        nullable=False,
        default=RelationshipType.PRIMARY_FOCUS,
        index=True,
    )

    evidence_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
