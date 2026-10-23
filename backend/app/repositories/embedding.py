from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.problem_embedding import ProblemEmbedding


def upsert_embedding(
    db: Session,
    problem_id: UUID,
    vector: list[float],
    model_name: str,
    model_dimensions: int,
    library_version: str,
    source_hash: str,
) -> None:
    row = db.get(ProblemEmbedding, problem_id)
    if row is None:
        row = ProblemEmbedding(problem_id=problem_id)
        db.add(row)
    row.embedding = vector
    row.model_name = model_name
    row.model_dimensions = model_dimensions
    row.library_version = library_version
    row.source_hash = source_hash
    row.embedded_at = datetime.now(timezone.utc)


def list_problems_with_embedding_state(db: Session) -> list[tuple[Problem, ProblemEmbedding | None]]:
    rows = db.execute(
        select(Problem, ProblemEmbedding)
        .outerjoin(ProblemEmbedding, ProblemEmbedding.problem_id == Problem.id)
        .order_by(Problem.created_at, Problem.id)
    ).all()
    return [(row[0], row[1]) for row in rows]


def count_embeddings(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(ProblemEmbedding)) or 0


def nearest_problems(
    db: Session,
    vector: list[float],
    min_similarity: float,
    limit: int,
    exclude_problem_id: UUID | None = None,
) -> list[tuple[UUID, float]]:
    """Problem ids nearest to `vector` by cosine similarity (1 = identical direction),
    keeping only those at or above `min_similarity`, best first."""
    distance = ProblemEmbedding.embedding.cosine_distance(vector)
    statement = (
        select(ProblemEmbedding.problem_id, (1 - distance).label("similarity"))
        .where(distance <= 1 - min_similarity)
        .order_by(distance, ProblemEmbedding.problem_id)
        .limit(limit)
    )
    if exclude_problem_id is not None:
        statement = statement.where(ProblemEmbedding.problem_id != exclude_problem_id)
    return [(row[0], float(row[1])) for row in db.execute(statement).all()]


def get_embedding_vector(db: Session, problem_id: UUID) -> list[float] | None:
    row = db.get(ProblemEmbedding, problem_id)
    return None if row is None else [float(v) for v in row.embedding]
