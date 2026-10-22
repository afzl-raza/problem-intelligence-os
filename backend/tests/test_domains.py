from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def test_list_domains_with_counts(client, db_session):
    ingest_dataset(db_session, {
        "default_domains": ["Parking Management SaaS"],
        "entries": [make_entry("Acme Parking", "Gate queues"), make_entry("Beta Park", "Permit paperwork")],
    })
    ingest_dataset(db_session, {"default_domains": ["Fintech"], "entries": [make_entry("Coin Co", "Slow settlement")]})

    res = client.get("/domains")
    assert res.status_code == status.HTTP_200_OK, res.text
    by_slug = {d["slug"]: d for d in res.json()}
    assert list(by_slug) == ["fintech", "parking-management-saas"]
    assert by_slug["parking-management-saas"]["name"] == "Parking Management SaaS"
    assert by_slug["parking-management-saas"]["problem_count"] == 2
    assert by_slug["parking-management-saas"]["company_count"] == 2
    assert by_slug["fintech"]["problem_count"] == 1


def test_company_counted_once_per_domain(client, db_session):
    # One company linked to two problems in the same domain counts once.
    ingest_dataset(db_session, {
        "default_domains": ["Parking Management SaaS"],
        "entries": [make_entry("Acme Parking", "Gate queues"), make_entry("Acme Parking", "Permit paperwork")],
    })

    domain = client.get("/domains/parking-management-saas").json()
    assert domain["problem_count"] == 2
    assert domain["company_count"] == 1


def test_get_domain_not_found(client):
    res = client.get("/domains/does-not-exist")
    assert res.status_code == status.HTTP_404_NOT_FOUND
