"""Keeping problem embeddings in step with problem text.

Indexing is an explicit command (`scripts/embed_problems.py`), not a side effect of
writes or requests: creating, updating, or ingesting problems never embeds anything,
it only leaves the affected vectors *stale*, which `find_stale` then reports.
"""
from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.problem_embedding import EMBEDDING_DIMENSIONS, ProblemEmbedding
from app.repositories.embedding import (
    count_embeddings,
    list_problems_with_embedding_state,
    upsert_embedding,
)
from app.services.embeddings import Embedder
from app.utils.deduplication import compute_content_hash


def embedding_source_text(problem: Problem) -> str:
    """The text a problem is embedded from: title, description, then category."""
    parts = [problem.title.strip()]
    if problem.description and problem.description.strip():
        parts.append(problem.description.strip())
    if problem.category and problem.category.strip():
        parts.append(problem.category.strip())
    return ". ".join(parts)


def source_hash(problem: Problem) -> str:
    return compute_content_hash(embedding_source_text(problem))


def is_stale(problem: Problem, embedding: ProblemEmbedding | None, embedder: Embedder) -> bool:
    return (
        embedding is None
        or embedding.source_hash != source_hash(problem)
        or embedding.model_name != embedder.name
        or embedding.model_dimensions != embedder.dimensions
    )


def find_stale(db: Session, embedder: Embedder) -> list[Problem]:
    return [p for p, e in list_problems_with_embedding_state(db) if is_stale(p, e, embedder)]


def reindex(db: Session, embedder: Embedder, force: bool = False, batch_size: int = 32) -> dict:
    """Embed every stale problem (or all of them with `force`). Idempotent: a second run
    with nothing changed embeds nothing."""
    if embedder.dimensions != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"embedder produces {embedder.dimensions}-dimensional vectors but the "
            f"problem_embeddings column is vector({EMBEDDING_DIMENSIONS})"
        )

    state = list_problems_with_embedding_state(db)
    todo = [p for p, e in state if force or is_stale(p, e, embedder)]

    for start in range(0, len(todo), batch_size):
        batch = todo[start : start + batch_size]
        vectors = embedder.embed_documents([embedding_source_text(p) for p in batch])
        for problem, vector in zip(batch, vectors, strict=True):
            upsert_embedding(
                db,
                problem_id=problem.id,
                vector=vector,
                model_name=embedder.name,
                model_dimensions=embedder.dimensions,
                library_version=embedder.library_version,
                source_hash=source_hash(problem),
            )
        db.commit()

    return {"total": len(state), "embedded": len(todo), "already_current": len(state) - len(todo)}


def status(db: Session, embedder: Embedder | None) -> dict:
    state = list_problems_with_embedding_state(db)
    indexed = count_embeddings(db)
    # Staleness is relative to a model, so it is unknown (None) while the provider is disabled.
    stale = None if embedder is None else len([1 for p, e in state if is_stale(p, e, embedder)])
    return {
        "available": embedder is not None and indexed > 0,
        "provider_enabled": embedder is not None,
        "model_name": embedder.name if embedder else None,
        "model_dimensions": embedder.dimensions if embedder else None,
        "total_problems": len(state),
        "indexed": indexed,
        "stale": stale,
    }
