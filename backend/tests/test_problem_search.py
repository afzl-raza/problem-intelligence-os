from fastapi import status


def test_search_ranks_title_match_above_description_match(client):
    client.post("/problems", json={
        "title": "Telemetry Pipeline Observability Gaps",
        "description": "Totally unrelated banking compliance workflow notes.",
    })
    client.post("/problems", json={
        "title": "Totally Unrelated Banking Compliance Workflow",
        "description": "Telemetry pipeline observability gaps are common in kubernetes clusters.",
    })

    res = client.get("/problems/search", params={"q": "telemetry pipeline observability"})
    assert res.status_code == status.HTTP_200_OK, res.text
    items = res.json()["items"]
    assert len(items) == 2
    assert items[0]["title"] == "Telemetry Pipeline Observability Gaps"
    assert items[0]["relevance_score"] > items[1]["relevance_score"]


def test_search_no_matches_returns_empty_paginated_result(client):
    client.post("/problems", json={"title": "Completely Different Topic"})

    res = client.get("/problems/search", params={"q": "zzzznonexistentqueryterm"})
    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_search_pagination(client):
    created_ids = set()
    for i in range(3):
        res = client.post("/problems", json={
            "title": f"Pagination Widget Term {i}",
            "description": "shared term widget pagination",
        })
        created_ids.add(res.json()["id"])

    page1 = client.get("/problems/search", params={"q": "pagination widget term", "limit": 2, "skip": 0})
    assert page1.status_code == status.HTTP_200_OK, page1.text
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2

    page2 = client.get("/problems/search", params={"q": "pagination widget term", "limit": 2, "skip": 2})
    assert page2.json()["total"] == 3
    assert len(page2.json()["items"]) == 1

    page1_ids = {item["id"] for item in page1.json()["items"]}
    page2_ids = {item["id"] for item in page2.json()["items"]}
    assert page1_ids.isdisjoint(page2_ids)
    assert page1_ids | page2_ids == created_ids


def test_search_blank_query_rejected(client):
    res = client.get("/problems/search", params={"q": ""})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_search_whitespace_query_rejected(client):
    res = client.get("/problems/search", params={"q": "   "})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
