from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def seed(db_session):
    ingest_dataset(db_session, {"default_domains": ["Parking Management SaaS"], "entries": [
        make_entry("ParkMobile", "Finding and paying for parking"),
        make_entry("Passport", "Curb enforcement for cities"),
    ]})


def test_suggest_autocompletes_substrings_across_kinds(client, db_session):
    seed(db_session)

    res = client.get("/search/suggest", params={"q": "park"})
    assert res.status_code == status.HTTP_200_OK, res.text
    found = {(s["kind"], s["label"]) for s in res.json()}

    assert ("company", "ParkMobile") in found
    assert ("problem", "Finding and paying for parking") in found
    assert ("domain", "Parking Management SaaS") in found


def test_suggest_tolerates_typos_and_reports_domain_slug(client, db_session):
    seed(db_session)

    suggestions = client.get("/search/suggest", params={"q": "parkng"}).json()

    domain = next(s for s in suggestions if s["kind"] == "domain")
    assert domain["value"] == "parking-management-saas"
    assert all(0 < s["score"] <= 1 for s in suggestions)


def test_suggest_respects_limit(client, db_session):
    seed(db_session)
    assert len(client.get("/search/suggest", params={"q": "park", "limit": 2}).json()) == 2


def test_spellcheck_corrects_misspelled_words(client, db_session):
    seed(db_session)

    data = client.get("/search/spellcheck", params={"q": "curb enforcment"}).json()

    assert data == {"query": "curb enforcment", "corrected": "curb enforcement"}


def test_spellcheck_returns_null_when_query_is_already_correct(client, db_session):
    seed(db_session)
    assert client.get("/search/spellcheck", params={"q": "parking"}).json()["corrected"] is None


def test_spellcheck_never_suggests_a_correction_with_no_results(client, db_session):
    seed(db_session)
    # 'zzqxw' has no close vocabulary word; nothing to correct, so no suggestion.
    assert client.get("/search/spellcheck", params={"q": "zzqxw"}).json()["corrected"] is None


def test_suggest_and_spellcheck_reject_blank_query(client):
    assert client.get("/search/suggest", params={"q": " "}).status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert client.get("/search/spellcheck", params={"q": " "}).status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
