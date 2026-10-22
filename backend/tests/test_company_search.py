from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def names(res):
    assert res.status_code == status.HTTP_200_OK, res.text
    return [item["name"] for item in res.json()["items"]]


def test_company_matches_on_own_profile(client):
    client.post("/companies", json={"name": "Gridlock Analytics", "industry": "Traffic data"})
    client.post("/companies", json={"name": "Unrelated Bakery", "industry": "Food"})

    assert names(client.get("/companies/search", params={"q": "traffic"})) == ["Gridlock Analytics"]


def test_company_matches_through_linked_problem(client, db_session):
    # Zeta Labs' own profile never mentions curbs; it is found via the problem it works on.
    ingest_dataset(db_session, {"entries": [
        make_entry("Zeta Labs", "Curb enforcement for cities",
                   company={"industry": "Software", "funding_stage": "seed"}),
    ]})
    client.post("/companies", json={"name": "Unlinked Co", "industry": "Software"})

    assert names(client.get("/companies/search", params={"q": "curb enforcement"})) == ["Zeta Labs"]


def test_company_search_funding_stage_filter_and_shape(client, db_session):
    ingest_dataset(db_session, {"entries": [
        make_entry("Seed Parking", "Gate queues", company={"industry": "Parking", "funding_stage": "seed"}),
        make_entry("Growth Parking", "Permit paperwork", company={"industry": "Parking", "funding_stage": "growth"}),
    ]})

    res = client.get("/companies/search", params={"q": "parking", "funding_stage": "growth"})
    assert names(res) == ["Growth Parking"]
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["relevance_score"] > 0
    assert data["items"][0]["funding_stage"] == "growth"


def test_company_search_rejects_blank_query(client):
    assert client.get("/companies/search", params={"q": "   "}).status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
