import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIMENSIONS = 384


class ProblemEmbedding(Base):
    """One semantic vector per problem, kept apart from `problems` so ordinary problem
    queries never load vectors, and so a model change is a re-index, not a schema change
    on `problems`. Model name, version and dimensions are recorded on every row."""

    __tablename__ = "problem_embeddings"
    __table_args__ = (
        Index(
            "ix_problem_embeddings_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    )

    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)

    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    library_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Hash of the text that was embedded; a mismatch with the current text means the vector is stale.
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    embedded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
