import logging

from fastapi import status
from sqlalchemy import func, select

from app.models.problem_embedding import ProblemEmbedding
from app.services.embedding_index import reindex
from app.services.embeddings import HashingEmbedder, set_embedder_override
from app.services.hybrid_search import reciprocal_rank_fusion
from factories import install_fixed_embeddings, make_entry
from app.services.research_ingestion import ingest_dataset

# Hand-set vectors (axes: 0 = "exit/checkout", 1 = "banking"). Cosine similarities:
#   gate~wait 0.994 | gate~mixed 0.861 | bank~wait 0.110 | bank~mixed 0.497 | gate~bank 0
GATE = [1.0, 0.0, 0.0]
BANK = [0.0, 1.0, 0.0]
MIXED = [0.8, 0.6, 0.0]
WAIT_QUERY = [0.9, 0.1, 0.0]  # "slow exit gate": close to GATE and MIXED, far from BANK


def problem(title, description, category="General", impact="medium"):
    return {"description": description, "category": category, "impact_level": impact}


def seed(db_session):
    ingest_dataset(db_session, {"default_domains": ["Mobility"], "entries": [
        make_entry("Gate Co", "Manual checkout friction", problem=problem("", "Staffed exits slow everyone down.", "Access", "high")),
        make_entry("Bank Co", "Bank account connectivity", problem=problem("", "Apps need account data.", "Banking", "medium")),
    ]})
    ingest_dataset(db_session, {"default_domains": ["Payments"], "entries": [
        make_entry("Mixed Co", "Paying at the barrier", problem=problem("", "Card readers at the barrier.", "Access", "high")),
    ]})
    return install_fixed_embeddings(
        db_session,
        {"Manual checkout friction": GATE, "Bank account connectivity": BANK, "Paying at the barrier": MIXED},
        {"slow exit gate": WAIT_QUERY, "checkout": GATE, "bank": BANK, "unrelated topic": [0.0, 0.0, 1.0]},
    )


def hybrid(client, q, **params):
    res = client.get("/problems/search", params={"q": q, "mode": "hybrid", **params})
    assert res.status_code == status.HTTP_200_OK, res.text
    return res.json()


def titles(data):
    return [item["title"] for item in data["items"]]


def test_reciprocal_rank_fusion_rewards_agreement_between_rankings():
    scores = reciprocal_rank_fusion(["a", "b", "c"], ["b", "d"], k=60)

    assert scores["b"] == 1 / 62 + 1 / 61  # ranked by both lists
    assert scores["b"] > scores["a"] > scores["c"]
    assert scores["d"] == 1 / 62
    assert set(scores) == {"a", "b", "c", "d"}


def test_semantic_match_found_without_any_shared_words(client, db_session):
    seed(db_session)

    keyword = client.get("/problems/search", params={"q": "slow exit gate"}).json()
    data = hybrid(client, "slow exit gate")

    assert keyword["items"] == []  # no stems in common
    assert data["mode_used"] == "hybrid" and data["semantic_note"] is None
    assert titles(data) == ["Manual checkout friction", "Paying at the barrier"]
    first = data["items"][0]
    assert first["match_type"] == "semantic" and first["similarity"] > 0.99
    assert data["items"][1]["similarity"] < first["similarity"]  # 0.861
    assert "Bank account connectivity" not in titles(data)  # 0.110 is below the threshold


def test_keyword_hits_are_never_lost_even_when_unrelated_by_meaning(client, db_session):
    seed(db_session)

    # "bank" matches Bank Co by keyword; its vector is also BANK, so it is both.
    both = hybrid(client, "bank")["items"][0]
    assert both["title"] == "Bank account connectivity" and both["match_type"] == "both"

    # A query whose vector is far from everything still returns exact keyword matches.
    set_embedder_override(install_fixed_embeddings(db_session, {}, {"checkout": [0.0, 0.0, 1.0]}))
    data = hybrid(client, "checkout")
    assert titles(data) == ["Manual checkout friction"]
    assert data["items"][0]["match_type"] == "keyword" and data["items"][0]["similarity"] is None


def test_every_keyword_result_is_present_in_hybrid(client, db_session):
    seed(db_session)
    keyword = {i["id"] for i in client.get("/problems/search", params={"q": "barrier OR bank OR checkout"}).json()["items"]}
    set_embedder_override(HashingEmbedder())
    reindex(db_session, HashingEmbedder(), force=True)

    assert keyword <= {i["id"] for i in hybrid(client, "barrier OR bank OR checkout")["items"]}


def test_filters_apply_to_hybrid_results_and_facets_ignore_them(client, db_session):
    seed(db_session)

    unfiltered = hybrid(client, "slow exit gate")
    only_payments = hybrid(client, "slow exit gate", domain="payments")
    high_access = hybrid(client, "slow exit gate", impact_level="high", category="access")

    assert titles(only_payments) == ["Paying at the barrier"] and only_payments["total"] == 1
    assert titles(high_access) == ["Manual checkout friction", "Paying at the barrier"]
    # Facets count the whole candidate set before filtering, so they match the unfiltered ones.
    assert only_payments["facets"] == unfiltered["facets"]
    assert {f["value"]: f["count"] for f in unfiltered["facets"]["domains"]} == {"mobility": 1, "payments": 1}


def test_pagination_is_stable_and_total_counts_the_filtered_union(client, db_session):
    seed(db_session)

    first = hybrid(client, "slow exit gate", limit=1, skip=0)
    second = hybrid(client, "slow exit gate", limit=1, skip=1)
    third = hybrid(client, "slow exit gate", limit=1, skip=2)

    assert first["total"] == second["total"] == 2
    assert titles(first) + titles(second) == ["Manual checkout friction", "Paying at the barrier"]
    assert third["items"] == []


def test_matches_below_the_similarity_threshold_are_dropped(client, db_session):
    seed(db_session)

    data = hybrid(client, "unrelated topic")

    assert data["items"] == [] and data["total"] == 0 and data["mode_used"] == "hybrid"


def test_query_is_embedded_once_and_problems_are_never_embedded_by_a_request(client, db_session):
    embedder = seed(db_session)
    calls = []
    original = embedder.embed_query
    embedder.embed_query = lambda text: (calls.append(text), original(text))[1]
    before = db_session.scalar(select(func.count()).select_from(ProblemEmbedding))
    stamps = {r.problem_id: r.embedded_at for r in db_session.scalars(select(ProblemEmbedding))}

    for params in ({}, {"limit": 1}, {"impact_level": "high"}):
        hybrid(client, "slow exit gate", **params)

    assert calls == ["slow exit gate"]
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(ProblemEmbedding)) == before
    assert {r.problem_id: r.embedded_at for r in db_session.scalars(select(ProblemEmbedding))} == stamps


def test_falls_back_to_keyword_when_semantic_search_is_disabled(client, db_session):
    seed(db_session)
    set_embedder_override(None)  # EMBEDDING_PROVIDER=none

    data = hybrid(client, "bank")

    assert data["mode_used"] == "keyword" and "turned off" in data["semantic_note"]
    assert titles(data) == ["Bank account connectivity"]
    assert data["items"][0]["match_type"] == "keyword"


def test_falls_back_to_keyword_when_nothing_is_indexed(client, db_session):
    ingest_dataset(db_session, {"entries": [make_entry("Bank Co", "Bank account connectivity")]})

    data = hybrid(client, "bank")

    assert data["mode_used"] == "keyword" and "no problems are indexed" in data["semantic_note"]
    assert titles(data) == ["Bank account connectivity"]


def test_falls_back_to_keyword_with_a_note_when_the_embedder_fails(client, db_session, caplog):
    embedder = seed(db_session)

    def broken(text):
        raise RuntimeError("model exploded")

    embedder.embed_query = broken
    with caplog.at_level(logging.ERROR):
        res = client.get("/problems/search", params={"q": "bank", "mode": "hybrid"})

    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["mode_used"] == "keyword" and "temporarily unavailable" in data["semantic_note"]
    assert titles(data) == ["Bank account connectivity"]
    # logged with the traceback, not swallowed silently
    assert any(r.exc_info and "model exploded" in str(r.exc_info[1]) for r in caplog.records)


def test_default_mode_is_keyword_and_unchanged(client, db_session):
    seed(db_session)

    data = client.get("/problems/search", params={"q": "slow exit gate"}).json()

    assert data["mode_used"] == "keyword" and data["semantic_note"] is None and data["items"] == []


def test_invalid_mode_is_rejected(client):
    res = client.get("/problems/search", params={"q": "bank", "mode": "magic"})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
