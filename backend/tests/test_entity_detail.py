import uuid

from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def seed(db_session):
    ingest_dataset(db_session, {"default_domains": ["Parking Management SaaS"], "entries": [
        make_entry("Acme Parking", "Gate queues"),
        make_entry("Beta Park", "Gate queues"),
        make_entry("Acme Parking", "Permit paperwork"),
    ]})


def test_problem_detail_has_domains_companies_and_sourced_evidence(client, db_session):
    seed(db_session)
    problem_id = client.get("/problems/search", params={"q": "gate queues"}).json()["items"][0]["id"]

    res = client.get(f"/problems/{problem_id}/detail")

    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert data["title"] == "Gate queues"
    assert data["domains"] == [{"slug": "parking-management-saas", "name": "Parking Management SaaS"}]
    assert sorted(c["name"] for c in data["companies"]) == ["Acme Parking", "Beta Park"]
    company = data["companies"][0]
    assert company["relationship_type"] == "primary_focus"
    evidence = company["evidence"][0]
    assert evidence["source"]["name"].endswith("Official Website")
    assert evidence["source"]["is_verified"] is False
    assert evidence["verification_status"] == "unverified"


def test_company_detail_groups_evidence_by_problem(client, db_session):
    seed(db_session)
    company_id = client.get("/companies/search", params={"q": "acme"}).json()["items"][0]["id"]

    data = client.get(f"/companies/{company_id}/detail").json()

    assert data["name"] == "Acme Parking"
    assert sorted(p["title"] for p in data["problems"]) == ["Gate queues", "Permit paperwork"]
    for problem in data["problems"]:
        assert problem["domains"][0]["slug"] == "parking-management-saas"
        assert len(problem["evidence"]) == 1
        assert problem["evidence"][0]["problem_id"] == problem["id"]


def test_unknown_ids_return_404_not_empty(client):
    missing = uuid.uuid4()
    assert client.get(f"/problems/{missing}/detail").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/companies/{missing}/detail").status_code == status.HTTP_404_NOT_FOUND


def test_linked_company_without_evidence_is_an_empty_list_not_an_error(client):
    problem_id = client.post("/problems", json={"title": "Orphan problem"}).json()["id"]
    company_id = client.post("/companies", json={"name": "Lonely Co"}).json()["id"]
    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})

    data = client.get(f"/problems/{problem_id}/detail").json()

    assert data["companies"][0]["evidence"] == []


def test_evidence_is_verified_only_with_a_verified_source_and_real_confidence(client):
    problem_id = client.post("/problems", json={"title": "Verified path"}).json()["id"]
    company_id = client.post("/companies", json={"name": "Solid Co"}).json()["id"]
    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})
    verified_source = client.post("/sources", json={"name": "Registry", "is_verified": True}).json()["id"]
    unverified_source = client.post("/sources", json={"name": "Blog", "is_verified": False}).json()["id"]

    def add(text, **extra):
        return client.post("/evidence", json={
            "company_id": company_id, "problem_id": problem_id,
            "evidence_text": text, "confidence_score": "high", **extra,
        })

    add("backed by registry", source_id=verified_source)
    add("backed by blog", source_id=unverified_source)
    add("no source at all")
    add("registry but flagged", source_id=verified_source, confidence_score="unverified")

    items = client.get(f"/companies/{company_id}/detail").json()["problems"][0]["evidence"]
    status_by_text = {i["evidence_text"]: i["verification_status"] for i in items}

    assert status_by_text == {
        "backed by registry": "verified",
        "backed by blog": "unverified",
        "no source at all": "unverified",
        "registry but flagged": "unverified",
    }
