import uuid
from fastapi import status


def test_create_source_success(client):
    payload = {
        "name": "Stripe Official Newsroom",
        "source_type": "company_website",
        "base_url": "https://stripe.com/newsroom",
        "is_verified": True,
    }
    response = client.post("/sources", json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["name"] == "Stripe Official Newsroom"
    assert data["source_type"] == "company_website"
    assert data["base_url"] == "https://stripe.com/newsroom"
    assert "id" in data
    assert uuid.UUID(data["id"])


def test_list_sources_pagination_filtering(client):
    client.post("/sources", json={"name": "TechCrunch Article", "source_type": "news_article"})
    client.post("/sources", json={"name": "ArXiv Paper 2408.01234", "source_type": "academic_paper"})
    client.post("/sources", json={"name": "GitHub Repository", "source_type": "code_repository"})

    # Filter by source_type
    res = client.get("/sources?source_type=news_article")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["name"] == "TechCrunch Article"

    # Filter by name substring
    res = client.get("/sources?name=ArXiv")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 1


def test_create_evidence_success(client):
    # Setup company, problem, and source
    c_res = client.post("/companies", json={"name": "Stripe"})
    p_res = client.post("/problems", json={"title": "Cross-Border Payment Latency"})
    s_res = client.post("/sources", json={"name": "Stripe Press Release", "source_type": "news_article"})

    company_id = c_res.json()["id"]
    problem_id = p_res.json()["id"]
    source_id = s_res.json()["id"]

    # Link company to problem first
    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})

    # Create evidence
    evidence_payload = {
        "company_id": company_id,
        "problem_id": problem_id,
        "source_id": source_id,
        "source_url": "https://stripe.com/newsroom/latam-expansion",
        "evidence_type": "official_doc",
        "evidence_text": "Stripe launched local acquisition in LatAm to reduce cross-border settlement latency from 4 days to instant.",
        "confidence_score": "high",
        "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }

    res = client.post("/evidence", json=evidence_payload)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    data = res.json()
    assert data["company_id"] == company_id
    assert data["problem_id"] == problem_id
    assert data["source_id"] == source_id
    assert data["confidence_score"] == "high"
    assert data["content_hash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_create_evidence_invalid_company_or_problem(client):
    non_existent_uuid = str(uuid.uuid4())
    p_res = client.post("/problems", json={"title": "Test Problem"})
    problem_id = p_res.json()["id"]

    evidence_payload = {
        "company_id": non_existent_uuid,
        "problem_id": problem_id,
        "evidence_text": "Invalid reference text",
    }
    res = client.post("/evidence", json=evidence_payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_get_evidence_for_link(client):
    c_res = client.post("/companies", json={"name": "Linear"})
    p_res = client.post("/problems", json={"title": "Issue Tracking Overhead"})
    company_id = c_res.json()["id"]
    problem_id = p_res.json()["id"]

    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})

    # Add 2 evidence records
    client.post("/evidence", json={
        "company_id": company_id,
        "problem_id": problem_id,
        "evidence_type": "official_doc",
        "evidence_text": "Linear documentation: fast issue tracking for software teams.",
        "confidence_score": "high",
    })
    client.post("/evidence", json={
        "company_id": company_id,
        "problem_id": problem_id,
        "evidence_type": "third_party_article",
        "evidence_text": "TechCrunch article describing Linear keyboard shortcuts.",
        "confidence_score": "medium",
    })

    # Query evidence for specific link
    res = client.get(f"/problems/{problem_id}/companies/{company_id}/evidence")
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert len(items) == 2


def test_delete_source_sets_evidence_source_id_to_null(client):
    c_res = client.post("/companies", json={"name": "Test Co"})
    p_res = client.post("/problems", json={"title": "Test Problem"})
    s_res = client.post("/sources", json={"name": "Temporary Source"})

    company_id = c_res.json()["id"]
    problem_id = p_res.json()["id"]
    source_id = s_res.json()["id"]

    ev_res = client.post("/evidence", json={
        "company_id": company_id,
        "problem_id": problem_id,
        "source_id": source_id,
        "evidence_text": "Evidence linked to temporary source",
    })
    evidence_id = ev_res.json()["id"]

    # Delete source
    del_s_res = client.delete(f"/sources/{source_id}")
    assert del_s_res.status_code == status.HTTP_204_NO_CONTENT

    # Evidence should still exist, but source_id is None
    ev_check = client.get(f"/evidence/{evidence_id}")
    assert ev_check.status_code == status.HTTP_200_OK
    assert ev_check.json()["source_id"] is None


def test_delete_company_cascades_and_removes_evidence(client):
    c_res = client.post("/companies", json={"name": "Company To Delete"})
    p_res = client.post("/problems", json={"title": "Problem To Retain"})

    company_id = c_res.json()["id"]
    problem_id = p_res.json()["id"]

    ev_res = client.post("/evidence", json={
        "company_id": company_id,
        "problem_id": problem_id,
        "evidence_text": "Evidence for company to delete",
    })
    evidence_id = ev_res.json()["id"]

    # Delete Company
    client.delete(f"/companies/{company_id}")

    # Evidence record should be deleted via CASCADE
    ev_check = client.get(f"/evidence/{evidence_id}")
    assert ev_check.status_code == status.HTTP_404_NOT_FOUND
