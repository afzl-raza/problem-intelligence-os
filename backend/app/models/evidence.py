from enum import Enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvidenceType(str, Enum):
    OFFICIAL_DOC = "official_doc"
    PRESS_RELEASE = "press_release"
    PRODUCT_PAGE = "product_page"
    PATENT_FILING = "patent_filing"
    USER_REVIEW = "user_review"
    THIRD_PARTY_ARTICLE = "third_party_article"
    JOB_LISTING = "job_listing"
    UNSPECIFIED = "unspecified"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("company_id", "problem_id", "content_hash", name="uq_evidence_company_problem_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    evidence_type: Mapped[EvidenceType] = mapped_column(
        SQLEnum(EvidenceType),
        nullable=False,
        default=EvidenceType.OFFICIAL_DOC,
        index=True,
    )

    evidence_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence_score: Mapped[ConfidenceLevel] = mapped_column(
        SQLEnum(ConfidenceLevel),
        nullable=False,
        default=ConfidenceLevel.HIGH,
        index=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
