from sqlalchemy import func, select

from app.models.company import Company
from app.models.domain import Domain, ProblemDomain
from app.models.evidence import ConfidenceLevel, EvidenceRecord
from app.models.problem import Problem
from app.models.source import Source
from app.services.research_ingestion import ingest_dataset
from factories import make_entry


def counts(db):
    return tuple(
        db.scalar(select(func.count()).select_from(model))
        for model in (Company, Problem, Source, EvidenceRecord, Domain, ProblemDomain)
    )


def test_ingestion_is_idempotent(db_session):
    dataset = {"default_domains": ["Parking Management SaaS"], "entries": [make_entry(), make_entry("Beta Park", "Permit paperwork")]}

    first = ingest_dataset(db_session, dataset)
    after_first = counts(db_session)
    second = ingest_dataset(db_session, dataset)

    assert after_first == (2, 2, 2, 2, 1, 2)
    assert counts(db_session) == after_first
    assert all(r["company_created"] and r["evidence_created"] for r in first)
    assert not any(r["company_created"] or r["problem_created"] or r["evidence_created"] for r in second)


def test_entry_domains_override_dataset_default(db_session):
    dataset = {
        "default_domains": ["Parking Management SaaS"],
        "entries": [make_entry(domains=["Fintech", "Smart Cities"])],
    }
    ingest_dataset(db_session, dataset)

    slugs = set(
        db_session.scalars(
            select(Domain.slug).join(ProblemDomain, ProblemDomain.domain_id == Domain.id)
        ).all()
    )
    assert slugs == {"fintech", "smart-cities"}


def test_research_data_is_never_marked_verified(db_session):
    ingest_dataset(db_session, {"entries": [make_entry()]})

    assert db_session.scalar(select(Source.is_verified)) is False
    assert db_session.scalar(select(EvidenceRecord.confidence_score)) == ConfidenceLevel.UNVERIFIED


def test_company_reused_across_legal_suffix_variants(db_session):
    ingest_dataset(db_session, {"entries": [make_entry("Acme Parking")]})
    results = ingest_dataset(db_session, {"entries": [make_entry("Acme Parking, Inc.", "A different problem")]})

    assert results[0]["company_created"] is False
    assert db_session.scalar(select(func.count()).select_from(Company)) == 1
