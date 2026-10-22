import uuid
from fastapi import status


def test_resolve_exact_normalized_match(client):
    client.post("/companies", json={"name": "Acme Corp"})

    res = client.get("/companies/resolve", params={"name": "Acme Corporation"})
    assert res.status_code == status.HTTP_200_OK, res.text
    matches = res.json()
    assert len(matches) >= 1
    assert matches[0]["name"] == "Acme Corp"
    assert matches[0]["is_exact_match"] is True
    assert matches[0]["similarity_score"] == 1.0


def test_resolve_fuzzy_match_above_threshold(client):
    client.post("/companies", json={"name": "Databricks"})

    res = client.get("/companies/resolve", params={"name": "Databrick", "min_similarity": 0.1})
    assert res.status_code == status.HTTP_200_OK, res.text
    matches = res.json()
    match = next((m for m in matches if m["name"] == "Databricks"), None)
    assert match is not None
    assert match["is_exact_match"] is False
    assert 0.0 < match["similarity_score"] <= 1.0


def test_resolve_fuzzy_match_below_threshold_excluded(client):
    client.post("/companies", json={"name": "Quantum Fusion Labs"})

    res = client.get("/companies/resolve", params={"name": "Banana Bread Bakery", "min_similarity": 0.3})
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json() == []


def test_resolve_deduplicates_candidates(client):
    created = client.post("/companies", json={"name": "Acme Corp"})
    company_id = created.json()["id"]

    # "Acme Corp" matches both the exact-normalized path and the fuzzy
    # (identical-string) path -- it must still appear only once.
    res = client.get("/companies/resolve", params={"name": "Acme Corp"})
    assert res.status_code == status.HTTP_200_OK, res.text
    ids = [m["id"] for m in res.json()]
    assert ids.count(company_id) == 1


def test_merge_reassigns_evidence_and_problem_links(client):
    keep_res = client.post("/companies", json={"name": "Keep Co"})
    dup_res = client.post("/companies", json={"name": "Duplicate Co"})
    problem_res = client.post("/problems", json={"title": "Merge Target Problem"})

    keep_id = keep_res.json()["id"]
    dup_id = dup_res.json()["id"]
    problem_id = problem_res.json()["id"]

    client.post(
        f"/problems/{problem_id}/companies/{dup_id}",
        json={"relationship_type": "primary_focus"},
    )

    ev_res = client.post("/evidence", json={
        "company_id": dup_id,
        "problem_id": problem_id,
        "evidence_text": "Evidence originally attached to the duplicate company.",
    })
    evidence_id = ev_res.json()["id"]

    merge_res = client.post("/companies/merge", json={
        "keep_company_id": keep_id,
        "duplicate_company_id": dup_id,
    })
    assert merge_res.status_code == status.HTTP_200_OK, merge_res.text
    assert merge_res.json()["merged_company_id"] == dup_id
    assert merge_res.json()["company"]["id"] == keep_id

    # Evidence reassigned to the surviving company
    ev_check = client.get(f"/evidence/{evidence_id}")
    assert ev_check.json()["company_id"] == keep_id

    # Problem link reassigned to the surviving company
    companies_for_problem = client.get(f"/problems/{problem_id}/companies").json()
    ids = [c["id"] for c in companies_for_problem]
    assert keep_id in ids
    assert dup_id not in ids

    # Duplicate company itself is gone
    dup_check = client.get(f"/companies/{dup_id}")
    assert dup_check.status_code == status.HTTP_404_NOT_FOUND


def test_merge_preserves_keep_company_relationship_on_collision(client):
    keep_res = client.post("/companies", json={"name": "Keep Collision Co"})
    dup_res = client.post("/companies", json={"name": "Duplicate Collision Co"})
    problem_res = client.post("/problems", json={"title": "Collision Problem"})

    keep_id = keep_res.json()["id"]
    dup_id = dup_res.json()["id"]
    problem_id = problem_res.json()["id"]

    # Both already linked to the same problem, with different relationship types.
    client.post(
        f"/problems/{problem_id}/companies/{keep_id}",
        json={"relationship_type": "primary_focus"},
    )
    client.post(
        f"/problems/{problem_id}/companies/{dup_id}",
        json={"relationship_type": "research_phase"},
    )

    merge_res = client.post("/companies/merge", json={
        "keep_company_id": keep_id,
        "duplicate_company_id": dup_id,
    })
    assert merge_res.status_code == status.HTTP_200_OK, merge_res.text

    companies_for_problem = client.get(f"/problems/{problem_id}/companies").json()
    keep_entries = [c for c in companies_for_problem if c["id"] == keep_id]
    assert len(keep_entries) == 1
    assert keep_entries[0]["relationship_type"] == "primary_focus"


def test_merge_not_found(client):
    keep_res = client.post("/companies", json={"name": "Solo Co"})
    keep_id = keep_res.json()["id"]
    non_existent_id = str(uuid.uuid4())

    res = client.post("/companies/merge", json={
        "keep_company_id": keep_id,
        "duplicate_company_id": non_existent_id,
    })
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_merge_self_rejected(client):
    res_co = client.post("/companies", json={"name": "Self Co"})
    company_id = res_co.json()["id"]

    res = client.post("/companies/merge", json={
        "keep_company_id": company_id,
        "duplicate_company_id": company_id,
    })
    assert res.status_code == status.HTTP_400_BAD_REQUEST
