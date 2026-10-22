import pytest
from fastapi import status

from app.services.research_ingestion import ingest_dataset
from factories import make_entry

SEARCH_ENDPOINTS = [
    "/problems/search",
    "/companies/search",
    "/search/suggest",
    "/search/spellcheck",
]

# Every optional text filter / name parameter that reaches a SQL comparison.
FILTER_PARAMS = [
    ("/problems/search", {"q": "parking", "domain": "\x00"}),
    ("/problems/search", {"q": "parking", "category": "\x00"}),
    ("/companies/resolve", {"name": "\x00"}),
    ("/companies", {"name": "\x00"}),
    ("/companies", {"industry": "\x00"}),
    ("/companies", {"country": "\x00"}),
    ("/problems", {"title": "\x00"}),
    ("/problems", {"category": "\x00"}),
    ("/sources", {"name": "\x00"}),
]

# Odd but legitimate input must never produce a database error.
MALFORMED_QUERIES = ['!!!', '"unbalanced', "((", "OR", "-", "'; DROP TABLE problems;--", "\U0001F697", "a" * 200]


@pytest.mark.parametrize("path", SEARCH_ENDPOINTS)
@pytest.mark.parametrize("query", ["\x00", "a\x00b", " \x00 "])
def test_nul_byte_in_search_query_is_rejected_not_a_500(client, path, query):
    res = client.get(path, params={"q": query})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, res.text


@pytest.mark.parametrize("path,params", FILTER_PARAMS)
def test_nul_byte_in_filter_parameter_is_rejected_not_a_500(client, path, params):
    res = client.get(path, params=params)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, res.text


@pytest.mark.parametrize("path", SEARCH_ENDPOINTS)
@pytest.mark.parametrize("query", MALFORMED_QUERIES)
def test_malformed_but_legitimate_queries_never_error(client, db_session, path, query):
    ingest_dataset(db_session, {"entries": [make_entry("Acme Parking", "Gate queue friction")]})

    res = client.get(path, params={"q": query})

    assert res.status_code == status.HTTP_200_OK, res.text


def test_query_over_length_limit_is_rejected(client):
    assert client.get("/problems/search", params={"q": "a" * 201}).status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_punctuation_only_query_returns_empty_results(client, db_session):
    ingest_dataset(db_session, {"entries": [make_entry()]})

    data = client.get("/problems/search", params={"q": "!!!"}).json()

    assert data["items"] == []
    assert data["total"] == 0
