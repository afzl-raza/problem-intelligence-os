from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def company(stage):
    return {"industry": "Parking", "funding_stage": stage}


def problem(impact, category, description="Details."):
    return {"description": description, "category": category, "impact_level": impact}


def seed(db_session):
    ingest_dataset(db_session, {"default_domains": ["Parking Management SaaS"], "entries": [
        make_entry("Acme Parking", "Gate queues", problem=problem("high", "Access"), company=company("seed")),
        make_entry("Beta Park", "Gate queues", problem=problem("high", "Access"), company=company("growth")),
        make_entry("Acme Parking", "Permit paperwork", problem=problem("medium", "Permits"), company=company("seed")),
        make_entry("Gamma Lot", "Meter payments", problem=problem("medium", "Payments"), company=company("unknown")),
    ]})
    ingest_dataset(db_session, {"default_domains": ["Fintech"], "entries": [
        make_entry("Coin Co", "Slow settlement", problem=problem("high", "Payments"), company=company("series_a")),
    ]})


def landscape(client, **params):
    res = client.get("/domains/parking-management-saas/landscape", params=params)
    assert res.status_code == status.HTTP_200_OK, res.text
    return res.json()


def test_landscape_aggregates(client, db_session):
    seed(db_session)
    data = landscape(client)

    assert data["domain"]["name"] == "Parking Management SaaS"
    assert {c["category"]: c["problem_count"] for c in data["categories"]} == {"Access": 1, "Permits": 1, "Payments": 1}
    assert {i["impact_level"]: i["problem_count"] for i in data["impact_distribution"]} == {"high": 1, "medium": 2}
    # Three distinct companies, even though Acme is linked to two problems.
    assert {f["funding_stage"]: f["company_count"] for f in data["funding_distribution"]} == {
        "seed": 1, "growth": 1, "unknown": 1,
    }
    by_name = {c["name"]: c["problem_count"] for c in data["companies"]}
    assert by_name == {"Acme Parking": 2, "Beta Park": 1, "Gamma Lot": 1}
    assert "Coin Co" not in by_name  # belongs to another domain


def test_landscape_counts_agree_with_domain_endpoints(client, db_session):
    seed(db_session)
    data = landscape(client)

    listed = {d["slug"]: d for d in client.get("/domains").json()}["parking-management-saas"]
    single = client.get("/domains/parking-management-saas").json()

    assert data["domain"] == listed == single
    assert data["problems_total"] == data["domain"]["problem_count"] == 3
    assert len(data["companies"]) == data["domain"]["company_count"] == 3


def test_landscape_problem_rows_carry_company_and_evidence_counts(client, db_session):
    seed(db_session)
    rows = {p["title"]: p for p in landscape(client)["problems"]}

    assert rows["Gate queues"]["company_count"] == 2
    assert rows["Gate queues"]["evidence_count"] == 2
    assert rows["Permit paperwork"]["company_count"] == 1
    # Everything ingested from research is unverified; the count says so explicitly.
    assert all(p["verified_evidence_count"] == 0 for p in rows.values())


def test_verified_count_uses_the_shared_rule(client, db_session):
    seed(db_session)
    gate = next(p for p in landscape(client)["problems"] if p["title"] == "Gate queues")
    company_id = client.get("/companies/search", params={"q": "acme"}).json()["items"][0]["id"]
    source_id = client.post("/sources", json={"name": "Registry", "is_verified": True}).json()["id"]

    client.post("/evidence", json={
        "company_id": company_id, "problem_id": gate["id"], "source_id": source_id,
        "evidence_text": "Confirmed by registry.", "confidence_score": "high",
    })

    row = next(p for p in landscape(client)["problems"] if p["title"] == "Gate queues")
    assert (row["evidence_count"], row["verified_evidence_count"]) == (3, 1)


def test_landscape_filters_and_pagination_keep_total_consistent(client, db_session):
    seed(db_session)

    assert [p["title"] for p in landscape(client, impact_level="high")["problems"]] == ["Gate queues"]
    assert [p["title"] for p in landscape(client, category="PERMITS")["problems"]] == ["Permit paperwork"]

    first = landscape(client, limit=2)
    second = landscape(client, limit=2, skip=2)
    assert first["problems_total"] == second["problems_total"] == 3
    assert len(first["problems"]) == 2 and len(second["problems"]) == 1
    titles = [p["title"] for p in first["problems"] + second["problems"]]
    assert titles == sorted(titles) and len(set(titles)) == 3


def test_every_link_in_the_landscape_resolves_to_a_detail_page(client, db_session):
    seed(db_session)
    data = landscape(client)

    for p in data["problems"]:
        assert client.get(f"/problems/{p['id']}/detail").status_code == status.HTTP_200_OK
    for c in data["companies"]:
        assert client.get(f"/companies/{c['id']}/detail").status_code == status.HTTP_200_OK


def test_unknown_domain_is_404_and_empty_filter_result_is_not(client, db_session):
    seed(db_session)
    assert client.get("/domains/nope/landscape").status_code == status.HTTP_404_NOT_FOUND

    data = landscape(client, category="Nonexistent")
    assert data["problems"] == [] and data["problems_total"] == 0
    assert data["domain"]["problem_count"] == 3  # domain-level counts ignore the list filter


def test_landscape_rejects_nul_in_filters(client, db_session):
    seed(db_session)
    res = client.get("/domains/parking-management-saas/landscape", params={"category": "\x00"})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
