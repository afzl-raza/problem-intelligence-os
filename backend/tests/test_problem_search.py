from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def titles(res):
    return sorted(item["title"] for item in res.json()["items"])


def test_search_supports_phrase_or_and_exclusion(client):
    for title in [
        "Curb enforcement for cities",
        "Enforcement of curb rules on campus",
        "Exit checkout friction",
        "Checkout lines at university garages",
    ]:
        client.post("/problems", json={"title": title})

    assert titles(client.get("/problems/search", params={"q": '"curb enforcement"'})) == ["Curb enforcement for cities"]
    assert len(client.get("/problems/search", params={"q": "curb OR checkout"}).json()["items"]) == 4
    assert titles(client.get("/problems/search", params={"q": "checkout -university"})) == ["Exit checkout friction"]


def _seed_filterable(db_session):
    def problem(title, impact, category="Parking"):
        return {"description": f"{title} details.", "category": category, "impact_level": impact}

    def company(stage):
        return {"industry": "Parking", "country": "United States", "funding_stage": stage}

    ingest_dataset(db_session, {"default_domains": ["Parking Management SaaS"], "entries": [
        make_entry("Gate Co", "Parking gate queues", problem=problem("Parking gate queues", "high"), company=company("seed")),
        make_entry("Permit Co", "Parking permit paperwork", problem=problem("Parking permit paperwork", "medium"), company=company("growth")),
    ]})
    ingest_dataset(db_session, {"default_domains": ["Fintech"], "entries": [
        make_entry("Fraud Co", "Parking payment fraud",
                   problem=problem("Parking payment fraud", "high", category="Payments"), company=company("series_a")),
    ]})


def test_search_filters(client, db_session):
    _seed_filterable(db_session)

    def search(**params):
        res = client.get("/problems/search", params={"q": "parking", **params})
        assert res.status_code == status.HTTP_200_OK, res.text
        return res.json()

    assert search()["total"] == 3
    assert {i["title"] for i in search(domain="parking-management-saas")["items"]} == {"Parking gate queues", "Parking permit paperwork"}
    assert search(impact_level="high")["total"] == 2
    assert [i["title"] for i in search(funding_stage="growth")["items"]] == ["Parking permit paperwork"]
    assert [i["title"] for i in search(category="PAYMENTS")["items"]] == ["Parking payment fraud"]
    assert search(domain="parking-management-saas", impact_level="high")["total"] == 1


def test_search_facets_count_text_matches_before_filters(client, db_session):
    _seed_filterable(db_session)

    facets = client.get("/problems/search", params={"q": "parking", "domain": "fintech"}).json()["facets"]

    assert {(f["value"], f["count"]) for f in facets["domains"]} == {("parking-management-saas", 2), ("fintech", 1)}
    assert {(f["value"], f["count"]) for f in facets["impact_levels"]} == {("high", 2), ("medium", 1)}
    assert {f["label"] for f in facets["domains"]} == {"Parking Management SaaS", "Fintech"}


def test_search_items_include_domains_and_sentinel_snippets(client, db_session):
    ingest_dataset(db_session, {"default_domains": ["Parking Management SaaS"], "entries": [
        make_entry("Gate Co", "Downtown congestion",
                   problem={"description": "Drivers struggle to find parking downtown.", "impact_level": "high"}),
    ]})

    item = client.get("/problems/search", params={"q": "parking"}).json()["items"][0]

    assert item["snippet"] == "Drivers struggle to find \x02parking\x03 downtown."
    assert "<" not in item["snippet"]
    assert item["domains"] == [{"slug": "parking-management-saas", "name": "Parking Management SaaS"}]


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
