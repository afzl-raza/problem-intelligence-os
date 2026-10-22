"""Idempotent ingestion of researched company/problem/evidence entries.

Shared by the CLI loader (scripts/ingest_research_data.py) and, later, the
in-app research pipeline's approval step, so both publish through exactly
the same rules. Every entity is get-or-created and nothing is ever deleted.

Research entries are paraphrases of a company's own marketing copy, not
independently verified facts, so every Source is forced to
is_verified=False and every EvidenceRecord to confidence_score=UNVERIFIED.
This is deliberately not a per-entry option.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company, FundingStage
from app.models.company_problem import RelationshipType
from app.models.evidence import ConfidenceLevel, EvidenceRecord, EvidenceType
from app.models.problem import ImpactLevel, Problem
from app.models.source import Source, SourceType
from app.schemas.company import CompanyCreate
from app.schemas.evidence import EvidenceCreate
from app.schemas.problem import CompanyProblemLink, ProblemCreate
from app.schemas.source import SourceCreate
from app.services.company import create_company
from app.services.domain import attach_problem_to_domain, get_or_create_domain
from app.services.evidence import create_evidence
from app.services.problem import create_problem, link_company_to_problem
from app.services.source import create_source
from app.utils.deduplication import compute_content_hash
from app.utils.entity_resolution import normalize_company_name


def get_or_create_company(db: Session, name: str, fields: dict) -> tuple[Company, bool]:
    existing = db.scalar(select(Company).where(Company.normalized_name == normalize_company_name(name)))
    if existing:
        return existing, False
    company = create_company(
        db=db,
        company_data=CompanyCreate(
            name=name,
            industry=fields.get("industry"),
            country=fields.get("country"),
            funding_stage=FundingStage(fields.get("funding_stage", "unknown")),
            website_url=fields.get("website_url"),
        ),
    )
    return company, True


def get_or_create_problem(db: Session, title: str, fields: dict) -> tuple[Problem, bool]:
    existing = db.scalar(select(Problem).where(Problem.title == title))
    if existing:
        return existing, False
    problem = create_problem(
        db=db,
        problem_data=ProblemCreate(
            title=title,
            description=fields.get("description"),
            category=fields.get("category"),
            impact_level=ImpactLevel(fields.get("impact_level", "unknown")),
        ),
    )
    return problem, True


def get_or_create_source(db: Session, name: str, fields: dict) -> tuple[Source, bool]:
    existing = db.scalar(select(Source).where(Source.name == name))
    if existing:
        return existing, False
    source = create_source(
        db=db,
        source_data=SourceCreate(
            name=name,
            source_type=SourceType(fields.get("source_type", "company_website")),
            base_url=fields.get("base_url"),
            is_verified=False,
        ),
    )
    return source, True


def get_or_create_evidence(
    db: Session,
    company: Company,
    problem: Problem,
    source: Source,
    evidence_text: str,
    source_url: str,
) -> tuple[EvidenceRecord, bool]:
    content_hash = compute_content_hash(evidence_text)
    existing = db.scalar(
        select(EvidenceRecord).where(
            EvidenceRecord.company_id == company.id,
            EvidenceRecord.problem_id == problem.id,
            EvidenceRecord.content_hash == content_hash,
        )
    )
    if existing:
        return existing, False

    evidence = create_evidence(
        db=db,
        evidence_data=EvidenceCreate(
            company_id=company.id,
            problem_id=problem.id,
            source_id=source.id,
            source_url=source_url,
            evidence_type=EvidenceType.PRODUCT_PAGE,
            evidence_text=evidence_text,
            confidence_score=ConfidenceLevel.UNVERIFIED,
            content_hash=content_hash,
        ),
    )
    if evidence is None:
        raise RuntimeError("Evidence creation failed: company, problem, or source vanished mid-ingestion")
    return evidence, True


def ingest_entry(db: Session, entry: dict, default_domains: list[str] | None = None) -> dict:
    """Ingest one research entry; returns what was created vs. reused."""
    company, company_created = get_or_create_company(db, entry["company_name"], entry["company"])
    problem, problem_created = get_or_create_problem(db, entry["problem_title"], entry["problem"])
    source, source_created = get_or_create_source(db, entry["source_name"], entry["source"])

    link_company_to_problem(
        db=db,
        problem_id=problem.id,
        company_id=company.id,
        link_data=CompanyProblemLink(
            relationship_type=RelationshipType(entry.get("relationship_type", "primary_focus")),
            evidence_summary=entry["relationship_note"],
        ),
    )

    _, evidence_created = get_or_create_evidence(
        db, company, problem, source, entry["evidence_text"], entry["source_url"]
    )

    domain_names = entry.get("domains") or default_domains or []
    domains_created = 0
    for domain_name in domain_names:
        domain, created = get_or_create_domain(db, domain_name)
        domains_created += int(created)
        attach_problem_to_domain(db, problem, domain)

    return {
        "company_name": entry["company_name"],
        "problem_title": entry["problem_title"],
        "company_created": company_created,
        "problem_created": problem_created,
        "source_created": source_created,
        "evidence_created": evidence_created,
        "domains_created": domains_created,
        "domains": domain_names,
    }


def ingest_dataset(db: Session, dataset: dict) -> list[dict]:
    default_domains = dataset.get("default_domains")
    return [ingest_entry(db, entry, default_domains) for entry in dataset["entries"]]
