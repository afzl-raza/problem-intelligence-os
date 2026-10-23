import uuid

from fastapi import status

from app.services.embedding_index import reindex
from app.services.embeddings import HashingEmbedder, set_embedder_override
from app.services.research_ingestion import ingest_dataset
from factories import install_fixed_embeddings, make_entry

# cosine similarities: A~C 0.80, B~C 0.60, A~B 0.00. RELATED_MIN_SIMILARITY is 0.70.
A, B, C = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.8, 0.6, 0.0]


def seed(db_session):
    ingest_dataset(db_session, {"default_domains": ["Mobility"], "entries": [
        make_entry("Co A", "Alpha problem"),
        make_entry("Co B", "Beta problem"),
        make_entry("Co C", "Gamma problem"),
    ]})
    return install_fixed_embeddings(db_session, {"Alpha problem": A, "Beta problem": B, "Gamma problem": C}, {})


def problem_id(client, title):
    return client.get("/problems/search", params={"q": title}).json()["items"][0]["id"]


def related(client, title, **params):
    res = client.get(f"/problems/{problem_id(client, title)}/related", params=params)
    assert res.status_code == status.HTTP_200_OK, res.text
    return res.json()


def test_related_problems_are_ranked_by_similarity_and_exclude_the_problem_itself(client, db_session):
    seed(db_session)

    data = related(client, "Alpha problem")

    assert data["semantic_available"] is True and data["min_similarity"] == 0.70
    assert [i["title"] for i in data["items"]] == ["Gamma problem"]  # 0.80; Beta is 0.00
    item = data["items"][0]
    assert abs(item["similarity"] - 0.8) < 1e-6
    assert item["domains"] == [{"slug": "mobility", "name": "Mobility"}]
    assert set(item) == {"id", "title", "category", "impact_level", "similarity", "domains"}


def test_related_problems_below_the_threshold_are_left_out(client, db_session):
    seed(db_session)

    # Gamma is 0.80 from Alpha but only 0.60 from Beta, which is under the 0.70 bar.
    assert [i["title"] for i in related(client, "Gamma problem")["items"]] == ["Alpha problem"]
    assert related(client, "Beta problem")["items"] == []


def test_related_respects_limit_and_returns_best_first(client, db_session):
    ingest_dataset(db_session, {"entries": [make_entry(f"Co {i}", f"Neighbour {i}") for i in range(4)]
                                + [make_entry("Hub Co", "Hub problem")]})
    install_fixed_embeddings(
        db_session,
        {"Hub problem": [1.0, 0.0, 0.0], "Neighbour 0": [1.0, 0.1, 0.0], "Neighbour 1": [1.0, 0.3, 0.0],
         "Neighbour 2": [1.0, 0.5, 0.0], "Neighbour 3": [1.0, 0.7, 0.0]},
        {},
    )

    data = related(client, "Hub problem", limit=2)

    assert [i["title"] for i in data["items"]] == ["Neighbour 0", "Neighbour 1"]
    assert data["items"][0]["similarity"] > data["items"][1]["similarity"]


def test_related_reports_unavailable_when_the_problem_is_not_indexed_or_search_is_off(client, db_session):
    ingest_dataset(db_session, {"entries": [make_entry("Co A", "Alpha problem")]})
    pid = problem_id(client, "Alpha problem")

    unindexed = client.get(f"/problems/{pid}/related").json()
    assert unindexed == {"items": [], "semantic_available": False, "min_similarity": 0.70}

    reindex(db_session, HashingEmbedder())
    set_embedder_override(None)
    assert client.get(f"/problems/{pid}/related").json()["semantic_available"] is False


def test_related_for_an_unknown_problem_is_404(client):
    assert client.get(f"/problems/{uuid.uuid4()}/related").status_code == status.HTTP_404_NOT_FOUND


def test_related_rejects_out_of_range_limit(client):
    res = client.get(f"/problems/{uuid.uuid4()}/related", params={"limit": 0})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_semantic_status_reflects_indexing_progress(client, db_session):
    ingest_dataset(db_session, {"entries": [make_entry("Co A", "Alpha problem"), make_entry("Co B", "Beta problem")]})

    before = client.get("/search/semantic/status").json()
    reindex(db_session, HashingEmbedder())
    after = client.get("/search/semantic/status").json()

    assert (before["total_problems"], before["indexed"], before["stale"], before["available"]) == (2, 0, 2, False)
    assert (after["indexed"], after["stale"], after["available"]) == (2, 0, True)
    assert after["model_name"] == "hashing-test" and after["model_dimensions"] == 384
    assert (after["semantic_min_similarity"], after["related_min_similarity"]) == (0.60, 0.70)


def test_semantic_status_when_the_provider_is_disabled(client, db_session):
    ingest_dataset(db_session, {"entries": [make_entry()]})
    set_embedder_override(None)

    data = client.get("/search/semantic/status").json()

    assert data["provider_enabled"] is False and data["available"] is False and data["model_name"] is None
    assert data["stale"] is None and data["indexed"] == 0  # staleness is unknowable without a model
