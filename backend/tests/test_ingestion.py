import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.company import Company
from app.models.company_problem import CompanyProblem
from app.models.evidence import EvidenceRecord, EvidenceType
from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
from app.models.problem import Problem
from app.models.source import Source
from app.services.ingestion import IngestionService
from app.utils.deduplication import compute_content_hash
from app.utils.security import UnsafeURLError, validate_safe_url


@pytest.fixture
def company_problem_pair(client):
    """Fixture returning an established company-problem link with valid UUIDs."""
    comp_res = client.post(
        "/companies",
        json={"name": "Ingestion Tech Inc", "industry": "Data Platform", "country": "USA"},
    )
    assert comp_res.status_code == 201
    company = comp_res.json()

    prob_res = client.post(
        "/problems",
        json={"title": "Data Ingestion Bottleneck", "category": "Pipeline", "impact_level": "high"},
    )
    assert prob_res.status_code == 201
    problem = prob_res.json()

    link_res = client.post(
        f"/problems/{problem['id']}/companies/{company['id']}",
        json={"relationship_type": "primary_focus"},
    )
    assert link_res.status_code == 201

    return company, problem


def test_validate_safe_url_ssrf_protection():
    """Verify validate_safe_url rejects loopback, private, and invalid schemes."""
    valid_url = "https://example.com/feed.xml"
    assert validate_safe_url(valid_url) == valid_url

    with pytest.raises(UnsafeURLError):
        validate_safe_url("http://127.0.0.1/admin")

    with pytest.raises(UnsafeURLError):
        validate_safe_url("http://localhost:8000/secret")

    with pytest.raises(UnsafeURLError):
        validate_safe_url("http://169.254.169.254/latest/meta-data")

    with pytest.raises(UnsafeURLError):
        validate_safe_url("ftp://example.com/data")


def test_rss_collector_ingestion_success(client, db_session, company_problem_pair):
    company, problem = company_problem_pair

    rss_xml = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
      <channel>
        <title>Tech News Feed</title>
        <link>https://example.com</link>
        <description>Testing RSS</description>
        <item>
          <title>Ingestion Tech Solves Bottlenecks</title>
          <description>Ingestion Tech Inc launched an automated data ingestion platform.</description>
          <link>https://example.com/news/1</link>
          <pubDate>Wed, 02 Sep 2026 00:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>"""

    # Trigger ingestion service directly with raw_xml mock payload
    from app.schemas.ingestion import RSSIngestionRequest
    req = RSSIngestionRequest(
        target_url="https://example.com/rss.xml",
        company_id=uuid.UUID(company["id"]),
        problem_id=uuid.UUID(problem["id"]),
    )

    run = IngestionService.run_rss_ingestion(db_session, req, raw_xml=rss_xml)
    assert run.status == IngestionStatus.COMPLETED
    assert run.items_extracted == 1
    assert run.items_ingested == 1
    assert run.items_skipped == 0

    # Verify EvidenceRecord in DB
    evidences = db_session.query(EvidenceRecord).filter_by(
        company_id=company["id"], problem_id=problem["id"]
    ).all()
    assert len(evidences) == 1
    assert "automated data ingestion platform" in evidences[0].evidence_text
    assert evidences[0].content_hash == compute_content_hash("Ingestion Tech Inc launched an automated data ingestion platform.")


def test_web_collector_ingestion_success(client, db_session, company_problem_pair):
    company, problem = company_problem_pair

    html_content = """<html>
    <head><title>Product Announcement</title></head>
    <body>
        <p>Ingestion Tech Inc releases new real-time streaming pipeline.</p>
    </body>
    </html>"""

    from app.schemas.ingestion import WebIngestionRequest
    req = WebIngestionRequest(
        target_url="https://example.com/product",
        company_id=uuid.UUID(company["id"]),
        problem_id=uuid.UUID(problem["id"]),
    )

    run = IngestionService.run_web_ingestion(db_session, req, raw_html=html_content)
    assert run.status == IngestionStatus.COMPLETED
    assert run.items_extracted == 1
    assert run.items_ingested == 1
    assert run.items_skipped == 0


def test_api_collector_ingestion_success(client, db_session, company_problem_pair):
    company, problem = company_problem_pair

    json_payload = """[
        {
            "title": "API News Item",
            "content": "Ingestion Tech API reduces data processing latency by 80 percent.",
            "url": "https://example.com/api/item/101"
        }
    ]"""

    from app.schemas.ingestion import APIIngestionRequest
    req = APIIngestionRequest(
        target_url="https://example.com/api/v1/news",
        company_id=uuid.UUID(company["id"]),
        problem_id=uuid.UUID(problem["id"]),
    )

    run = IngestionService.run_api_ingestion(db_session, req, raw_json=json_payload)
    assert run.status == IngestionStatus.COMPLETED
    assert run.items_extracted == 1
    assert run.items_ingested == 1
    assert run.items_skipped == 0


def test_ssrf_endpoint_protection(client, company_problem_pair):
    company, problem = company_problem_pair

    res = client.post(
        "/ingestion/web",
        json={
            "target_url": "http://127.0.0.1/admin",
            "company_id": company["id"],
            "problem_id": problem["id"],
        },
    )
    assert res.status_code == 400
    assert "SSRF" in res.json()["detail"] or "Security" in res.json()["detail"]


def test_ingestion_invalid_company_problem_link(client):
    fake_comp_id = str(uuid.uuid4())
    fake_prob_id = str(uuid.uuid4())

    res = client.post(
        "/ingestion/rss",
        json={
            "target_url": "https://example.com/rss",
            "company_id": fake_comp_id,
            "problem_id": fake_prob_id,
        },
    )
    assert res.status_code == 404


def test_ingestion_duplicate_skipping(client, db_session, company_problem_pair):
    company, problem = company_problem_pair

    rss_xml = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
      <channel>
        <title>Repeated News</title>
        <item>
          <title>Static News</title>
          <description>Identical article content repeated across runs.</description>
          <link>https://example.com/static</link>
        </item>
      </channel>
    </rss>"""

    from app.schemas.ingestion import RSSIngestionRequest
    req = RSSIngestionRequest(
        target_url="https://example.com/rss.xml",
        company_id=uuid.UUID(company["id"]),
        problem_id=uuid.UUID(problem["id"]),
    )

    # First run: should extract 1, ingest 1, skip 0
    run1 = IngestionService.run_rss_ingestion(db_session, req, raw_xml=rss_xml)
    assert run1.items_extracted == 1
    assert run1.items_ingested == 1
    assert run1.items_skipped == 0

    # Second run: exact same feed content -> should extract 1, ingest 0, skip 1
    run2 = IngestionService.run_rss_ingestion(db_session, req, raw_xml=rss_xml)
    assert run2.items_extracted == 1
    assert run2.items_ingested == 0
    assert run2.items_skipped == 1

    # Ensure DB only has 1 evidence record total
    count = db_session.query(EvidenceRecord).filter_by(
        company_id=company["id"], problem_id=problem["id"]
    ).count()
    assert count == 1


def test_db_composite_unique_constraint(db_session, company_problem_pair):
    company, problem = company_problem_pair

    c_hash = compute_content_hash("Unique evidence test snippet")

    rec1 = EvidenceRecord(
        company_id=uuid.UUID(company["id"]),
        problem_id=uuid.UUID(problem["id"]),
        evidence_text="Unique evidence test snippet",
        content_hash=c_hash,
    )
    db_session.add(rec1)
    db_session.commit()

    rec2 = EvidenceRecord(
        company_id=uuid.UUID(company["id"]),
        problem_id=uuid.UUID(problem["id"]),
        evidence_text="Unique evidence test snippet",
        content_hash=c_hash,
    )
    db_session.add(rec2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_source_deletion_sets_ingestion_run_source_id_to_null(client, db_session):
    # Register source
    s_res = client.post("/sources", json={"name": "Ingestion Source", "source_type": "news_article"})
    assert s_res.status_code == 201
    source_id = uuid.UUID(s_res.json()["id"])

    # Create ingestion run linked to source
    run = IngestionRun(
        source_id=source_id,
        status=IngestionStatus.COMPLETED,
        ingestion_type=IngestionType.RSS,
    )
    db_session.add(run)
    db_session.commit()
    run_id = run.id

    # Delete source via API
    del_res = client.delete(f"/sources/{source_id}")
    assert del_res.status_code == 204

    # Verify IngestionRun still exists and source_id is None
    db_session.expire_all()
    updated_run = db_session.query(IngestionRun).filter_by(id=run_id).first()
    assert updated_run is not None
    assert updated_run.source_id is None


def test_list_ingestion_runs_pagination_filtering(client, db_session):
    # Create sample runs
    for i in range(5):
        db_session.add(
            IngestionRun(
                status=IngestionStatus.COMPLETED if i % 2 == 0 else IngestionStatus.FAILED,
                ingestion_type=IngestionType.RSS if i < 3 else IngestionType.WEB_PAGE,
                items_extracted=i + 1,
                items_ingested=i,
            )
        )
    db_session.commit()

    # List all runs paginated
    res = client.get("/ingestion/runs?limit=3&skip=0")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
    assert body["skip"] == 0
    assert body["limit"] == 3

    # Filter by status
    status_res = client.get(f"/ingestion/runs?status={IngestionStatus.COMPLETED.value}")
    assert status_res.status_code == 200
    assert status_res.json()["total"] == 3


def test_ingestion_invalid_source_id(client, company_problem_pair):
    company, problem = company_problem_pair
    fake_source_id = str(uuid.uuid4())

    res = client.post(
        "/ingestion/rss",
        json={
            "target_url": "https://example.com/rss",
            "company_id": company["id"],
            "problem_id": problem["id"],
            "source_id": fake_source_id,
        },
    )
    assert res.status_code == 404
    assert f"Source with id '{fake_source_id}' not found." in res.json()["detail"]

