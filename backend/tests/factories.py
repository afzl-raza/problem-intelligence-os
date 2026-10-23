from sqlalchemy import select

from app.models.problem import Problem
from app.services.embedding_index import embedding_source_text, reindex
from app.services.embeddings import FixedEmbedder, set_embedder_override


def make_entry(company_name="Acme Parking", problem_title="Gate queue friction", **overrides):
    """A research-data entry in the scripts/research_data/*.json format."""
    entry = {
        "company_name": company_name,
        "company": {"industry": "Parking", "country": "United States", "funding_stage": "seed"},
        "problem_title": problem_title,
        "problem": {"description": "Drivers queue at exit gates.", "category": "Parking", "impact_level": "medium"},
        "source_name": f"{company_name} -- Official Website",
        "source": {"source_type": "company_website", "base_url": "https://example.com"},
        "source_url": "https://example.com/product",
        "evidence_text": f"{company_name} says it removes exit-gate queues.",
        "relationship_note": "Primary focus per official site.",
    }
    entry.update(overrides)
    return entry


def install_fixed_embeddings(db_session, problem_vectors: dict[str, list[float]], query_vectors: dict[str, list[float]]):
    """Embed the problems named in `problem_vectors` (title -> vector) with hand-set vectors, and make
    `query_vectors` (query text -> vector) the embedder's known queries. Returns the installed embedder.

    Cosine similarities are then exactly what the test author set, so ranking and threshold
    behaviour can be asserted without a real model."""
    problems = db_session.scalars(select(Problem)).all()
    texts = {embedding_source_text(p): problem_vectors[p.title] for p in problems if p.title in problem_vectors}
    embedder = FixedEmbedder({**texts, **query_vectors})
    set_embedder_override(embedder)
    reindex(db_session, embedder)
    return embedder
