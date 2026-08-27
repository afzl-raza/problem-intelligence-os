import uuid
from fastapi import status


def test_create_problem_success(client):
    payload = {
        "title": "Cross-Border Payment Settlement Latency",
        "description": "Cross-border B2B payments take 3-5 business days to clear in LatAm region.",
        "category": "FinTech",
        "domain_tags": ["fintech", "payments", "cross-border", "latam"],
        "impact_level": "high",
    }

    response = client.post("/problems", json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["title"] == "Cross-Border Payment Settlement Latency"
    assert data["category"] == "FinTech"
    assert data["impact_level"] == "high"
    assert data["domain_tags"] == ["fintech", "payments", "cross-border", "latam"]
    assert "id" in data
    assert uuid.UUID(data["id"])


def test_get_problem_by_id_success(client):
    create_res = client.post(
        "/problems",
        json={"title": "High LLM Inference Cost", "category": "AI Infrastructure"},
    )
    problem_id = create_res.json()["id"]

    response = client.get(f"/problems/{problem_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "High LLM Inference Cost"


def test_get_problem_not_found(client):
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/problems/{random_uuid}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Problem not found"


def test_get_problem_invalid_uuid(client):
    response = client.get("/problems/not-a-valid-uuid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_problem_invalid_impact_level(client):
    payload = {
        "title": "Invalid Impact",
        "impact_level": "super_catastrophic",  # Invalid enum value
    }
    response = client.post("/problems", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_problems_pagination_envelope(client):
    for i in range(3):
        client.post("/problems", json={"title": f"Problem Statement {i+1}"})

    response = client.get("/problems?skip=0&limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["total"] == 3
    assert data["skip"] == 0
    assert data["limit"] == 2
    assert len(data["items"]) == 2


def test_list_problems_filtering(client):
    client.post("/problems", json={"title": "Database Locking Bottlenecks", "category": "Databases", "impact_level": "critical"})
    client.post("/problems", json={"title": "Slow Frontend Bundle Load", "category": "Web Perf", "impact_level": "medium"})
    client.post("/problems", json={"title": "Database Connection Pool Exhaustion", "category": "Databases", "impact_level": "critical"})

    # Substring search on title
    res = client.get("/problems?title=Database")
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # Category filter
    res = client.get("/problems?category=Web Perf")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "Slow Frontend Bundle Load"

    # Enum impact_level filter
    res = client.get("/problems?impact_level=critical")
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_patch_problem_success(client):
    create_res = client.post(
        "/problems",
        json={"title": "Original Problem", "category": "DevTools"},
    )
    problem_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/problems/{problem_id}",
        json={"title": "Updated Problem Title", "impact_level": "high"},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    data = patch_res.json()
    assert data["title"] == "Updated Problem Title"
    assert data["category"] == "DevTools"  # Unchanged
    assert data["impact_level"] == "high"


def test_delete_problem_success(client):
    create_res = client.post("/problems", json={"title": "Temporary Problem"})
    problem_id = create_res.json()["id"]

    del_res = client.delete(f"/problems/{problem_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    get_res = client.get(f"/problems/{problem_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


# Company <-> Problem Association Tests

def test_link_company_to_problem_success(client):
    # Setup company and problem
    company_res = client.post("/companies", json={"name": "Stripe", "industry": "FinTech"})
    problem_res = client.post("/problems", json={"title": "Payment Latency", "category": "FinTech"})

    company_id = company_res.json()["id"]
    problem_id = problem_res.json()["id"]

    # Link
    link_payload = {
        "relationship_type": "primary_focus",
        "evidence_summary": "Stripe built universal API suite to solve online merchant settlement delays.",
    }
    link_res = client.post(
        f"/problems/{problem_id}/companies/{company_id}",
        json=link_payload,
    )
    assert link_res.status_code == status.HTTP_201_CREATED, link_res.text
    link_data = link_res.json()
    assert link_data["company_id"] == company_id
    assert link_data["problem_id"] == problem_id
    assert link_data["relationship_type"] == "primary_focus"

    # Query problems for company
    c_prob_res = client.get(f"/companies/{company_id}/problems")
    assert c_prob_res.status_code == status.HTTP_200_OK
    assert len(c_prob_res.json()) == 1
    assert c_prob_res.json()[0]["title"] == "Payment Latency"

    # Query companies for problem
    p_comp_res = client.get(f"/problems/{problem_id}/companies")
    assert p_comp_res.status_code == status.HTTP_200_OK
    assert len(p_comp_res.json()) == 1
    assert p_comp_res.json()[0]["name"] == "Stripe"


def test_unlink_company_from_problem_success(client):
    company_res = client.post("/companies", json={"name": "Linear"})
    problem_res = client.post("/problems", json={"title": "Issue Tracking Complexity"})

    company_id = company_res.json()["id"]
    problem_id = problem_res.json()["id"]

    # Link first
    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})

    # Unlink
    unlink_res = client.delete(f"/problems/{problem_id}/companies/{company_id}")
    assert unlink_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify company has no problems linked
    c_prob_res = client.get(f"/companies/{company_id}/problems")
    assert c_prob_res.status_code == status.HTTP_200_OK
    assert len(c_prob_res.json()) == 0


def test_cascade_delete_company_removes_link(client):
    company_res = client.post("/companies", json={"name": "Ephemeral Co"})
    problem_res = client.post("/problems", json={"title": "Ephemeral Problem"})

    company_id = company_res.json()["id"]
    problem_id = problem_res.json()["id"]

    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})

    # Delete Company
    client.delete(f"/companies/{company_id}")

    # Verify problem still exists but has 0 companies linked
    p_comp_res = client.get(f"/problems/{problem_id}/companies")
    assert p_comp_res.status_code == status.HTTP_200_OK
    assert len(p_comp_res.json()) == 0


def test_cascade_delete_problem_removes_link(client):
    company_res = client.post("/companies", json={"name": "Persistent Co"})
    problem_res = client.post("/problems", json={"title": "Target Problem"})

    company_id = company_res.json()["id"]
    problem_id = problem_res.json()["id"]

    client.post(f"/problems/{problem_id}/companies/{company_id}", json={})

    # Delete Problem
    client.delete(f"/problems/{problem_id}")

    # Verify company still exists but has 0 problems linked
    c_prob_res = client.get(f"/companies/{company_id}/problems")
    assert c_prob_res.status_code == status.HTTP_200_OK
    assert len(c_prob_res.json()) == 0
