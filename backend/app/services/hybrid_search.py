"""Hybrid (keyword + meaning) problem search, related problems, and semantic status.

Hybrid search merges two ranked candidate lists with Reciprocal Rank Fusion:
  * keyword candidates (Postgres full-text, the same ranking as mode=keyword), and
  * semantic candidates (pgvector cosine similarity >= SEMANTIC_MIN_SIMILARITY).
Every keyword hit stays in the result, so exact matches are never lost. If semantic
search cannot run (disabled, nothing indexed, model unavailable) the request degrades
to plain keyword results with an explanatory note instead of failing.

Only the *query* is embedded here, and only for hybrid requests; problems are never
embedded in request handling (see app.services.embedding_index).
"""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company import FundingStage
from app.models.problem import ImpactLevel
from app.repositories.detail import domains_for_problems
from app.repositories.embedding import count_embeddings, get_embedding_vector, nearest_problems
from app.repositories.problem import (
    facets_for_ids,
    filter_problem_ids,
    get_problem,
    get_problems_by_ids,
    hydrate_problems,
    keyword_candidate_ids,
)
from app.schemas.problem import ProblemResponse
from app.services import embedding_index
from app.services.embeddings import embed_query_cached, get_embedder
from app.services.problem import search_problems

logger = logging.getLogger(__name__)

RRF_K = 60
CANDIDATES = 50


def reciprocal_rank_fusion(*rankings: list[UUID], k: int = RRF_K) -> dict[UUID, float]:
    """score(id) = sum over rankings of 1 / (k + rank), rank starting at 1."""
    scores: dict[UUID, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return scores


def search_problems_hybrid(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 20,
    domain_slug: str | None = None,
    category: str | None = None,
    impact_level: ImpactLevel | None = None,
    funding_stage: FundingStage | None = None,
) -> dict:
    def keyword_fallback(note: str) -> dict:
        result = search_problems(
            db,
            query,
            skip=skip,
            limit=limit,
            domain_slug=domain_slug,
            category=category,
            impact_level=impact_level,
            funding_stage=funding_stage,
        )
        return {**result, "mode_used": "keyword", "semantic_note": note}

    embedder = get_embedder()
    if embedder is None:
        return keyword_fallback("Meaning-based search is turned off on this server; showing keyword results.")
    if count_embeddings(db) == 0:
        return keyword_fallback("Meaning-based search isn't set up yet (no problems are indexed); showing keyword results.")
    try:
        query_vector = embed_query_cached(embedder, query)
    except Exception:
        logger.exception("Embedding the search query failed; falling back to keyword search")
        return keyword_fallback("Meaning-based search is temporarily unavailable; showing keyword results.")

    semantic = nearest_problems(db, query_vector, settings.SEMANTIC_MIN_SIMILARITY, CANDIDATES)
    similarity = dict(semantic)
    keyword_ids = keyword_candidate_ids(db, query, CANDIDATES)
    fused = reciprocal_rank_fusion(keyword_ids, [problem_id for problem_id, _ in semantic])

    # Highest fused score first; ties broken by id so pagination is stable.
    ordered = sorted(fused, key=lambda problem_id: (-fused[problem_id], -problem_id.int))

    # Facets describe the whole candidate set; filters then narrow it (the same rule as keyword search).
    facets = facets_for_ids(db, ordered)
    allowed = filter_problem_ids(db, ordered, domain_slug, category, impact_level, funding_stage)
    filtered = [problem_id for problem_id in ordered if problem_id in allowed]

    page_ids = filtered[skip : skip + limit]
    hydrated = hydrate_problems(db, page_ids, query)
    keyword_set = set(keyword_ids)

    items = []
    for problem_id in page_ids:
        row = hydrated[problem_id]
        in_keyword, in_semantic = problem_id in keyword_set, problem_id in similarity
        items.append(
            {
                **ProblemResponse.model_validate(row["problem"], from_attributes=True).model_dump(),
                "relevance_score": fused[problem_id],
                "snippet": row["snippet"],
                "title_snippet": row["title_snippet"],
                "domains": row["domains"],
                "match_type": "both" if in_keyword and in_semantic else "keyword" if in_keyword else "semantic",
                "similarity": similarity.get(problem_id),
            }
        )

    return {
        "items": items,
        "total": len(filtered),
        "skip": skip,
        "limit": limit,
        "facets": facets,
        "mode_used": "hybrid",
        "semantic_note": None,
    }


def get_related_problems(db: Session, problem_id: UUID, limit: int = 5) -> dict | None:
    """Problems whose text is closest in meaning to this one. None if the problem doesn't exist."""
    if get_problem(db, problem_id) is None:
        return None

    unavailable = {"items": [], "semantic_available": False, "min_similarity": settings.RELATED_MIN_SIMILARITY}
    embedder = get_embedder()
    vector = get_embedding_vector(db, problem_id) if embedder is not None else None
    if vector is None:
        return unavailable

    neighbours = nearest_problems(
        db, vector, settings.RELATED_MIN_SIMILARITY, limit, exclude_problem_id=problem_id
    )
    problems = get_problems_by_ids(db, [other for other, _ in neighbours])
    domains = domains_for_problems(db, list(problems))
    return {
        "items": [
            {
                "id": other,
                "title": problems[other].title,
                "category": problems[other].category,
                "impact_level": problems[other].impact_level,
                "similarity": sim,
                "domains": domains[other],
            }
            for other, sim in neighbours
        ],
        "semantic_available": True,
        "min_similarity": settings.RELATED_MIN_SIMILARITY,
    }


def get_semantic_status(db: Session) -> dict:
    return {
        **embedding_index.status(db, get_embedder()),
        "semantic_min_similarity": settings.SEMANTIC_MIN_SIMILARITY,
        "related_min_similarity": settings.RELATED_MIN_SIMILARITY,
    }
