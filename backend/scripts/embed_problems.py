"""Embed problems for semantic search.

Embeds every problem whose vector is missing or stale (its text changed, or it was
embedded by a different model). Safe to re-run: with nothing changed it embeds
nothing. Embedding never happens inside API requests, so run this after adding or
editing problems.

Usage (from the backend directory):
    .venv\\Scripts\\python.exe scripts\\embed_problems.py            # only missing / stale
    .venv\\Scripts\\python.exe scripts\\embed_problems.py --force    # re-embed everything

The first run downloads the model (BAAI/bge-small-en-v1.5, ~130MB) into
backend/.model_cache.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal, engine  # noqa: E402
from app.services.embedding_index import find_stale, reindex, status  # noqa: E402
from app.services.embeddings import EmbeddingUnavailable, get_embedder  # noqa: E402


def run(force: bool = False) -> int:
    engine.echo = False  # settings.DEBUG would otherwise print every SQL statement
    embedder = get_embedder()
    if embedder is None:
        print("Semantic search is disabled (EMBEDDING_PROVIDER=none); nothing to do.")
        return 1

    db = SessionLocal()
    try:
        stale = len(find_stale(db, embedder))
        print(f"Model: {embedder.name} ({embedder.dimensions} dimensions)")
        print(f"{stale} problem(s) need embedding" + (" (forcing all)" if force else "") + "...")
        try:
            report = reindex(db, embedder, force=force)
        except EmbeddingUnavailable as error:
            print(f"Cannot embed: {error}")
            return 1
        print(f"Embedded {report['embedded']}; {report['already_current']} already current.")
        final = status(db, embedder)
        print(f"Index: {final['indexed']}/{final['total_problems']} problems indexed, {final['stale']} stale.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run(force="--force" in sys.argv[1:]))
