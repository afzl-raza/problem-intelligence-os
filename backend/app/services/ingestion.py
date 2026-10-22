from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.api import APICollector
from app.collectors.base import CollectedItem
from app.collectors.rss import RSSCollector
from app.collectors.web import WebCollector
from app.models.company import Company
from app.models.company_problem import CompanyProblem
from app.models.evidence import ConfidenceLevel, EvidenceRecord, EvidenceType
from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
from app.models.problem import Problem
from app.models.source import Source
from app.repositories.ingestion_run import IngestionRunRepository
from app.schemas.ingestion import (
    APIIngestionRequest,
    RSSIngestionRequest,
    WebIngestionRequest,
)
from app.utils.deduplication import compute_content_hash
from app.utils.security import UnsafeURLError, validate_safe_url


class IngestionService:
    """Service layer orchestrating multi-source ingestion pipelines."""

    @staticmethod
    def _validate_ingestion_target(
        db: Session, company_id: UUID, problem_id: UUID, source_id: UUID | None = None
    ) -> None:
        """Verify that Company, Problem, CompanyProblem junction link, and optional Source exist."""
        company = db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with id '{company_id}' not found.",
            )

        problem = db.execute(select(Problem).where(Problem.id == problem_id)).scalar_one_or_none()
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Problem with id '{problem_id}' not found.",
            )

        link = db.execute(
            select(CompanyProblem).where(
                CompanyProblem.company_id == company_id,
                CompanyProblem.problem_id == problem_id,
            )
        ).scalar_one_or_none()

        if not link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active Company-Problem link exists between company '{company_id}' and problem '{problem_id}'.",
            )

        if source_id is not None:
            source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
            if not source:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source with id '{source_id}' not found.",
                )

    @classmethod
    def run_rss_ingestion(
        cls, db: Session, req: RSSIngestionRequest, raw_xml: str | None = None
    ) -> IngestionRun:
        cls._validate_ingestion_target(db, req.company_id, req.problem_id, req.source_id)

        try:
            validate_safe_url(req.target_url)
        except UnsafeURLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security SSRF validation failed: {e}",
            )

        run = IngestionRunRepository.create(
            db=db, source_id=req.source_id, ingestion_type=IngestionType.RSS
        )

        try:
            collector = RSSCollector(raw_content=raw_xml)
            items = collector.collect(req.target_url)
            return cls._process_collected_items(db, run, req, items, EvidenceType.THIRD_PARTY_ARTICLE)
        except Exception as err:
            IngestionRunRepository.update_run_result(
                db=db,
                run=run,
                status=IngestionStatus.FAILED,
                error_message=str(err),
            )
            if isinstance(err, HTTPException):
                raise err
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"RSS Ingestion execution failed: {err}",
            )

    @classmethod
    def run_web_ingestion(
        cls, db: Session, req: WebIngestionRequest, raw_html: str | None = None
    ) -> IngestionRun:
        cls._validate_ingestion_target(db, req.company_id, req.problem_id, req.source_id)

        try:
            validate_safe_url(req.target_url)
        except UnsafeURLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security SSRF validation failed: {e}",
            )

        run = IngestionRunRepository.create(
            db=db, source_id=req.source_id, ingestion_type=IngestionType.WEB_PAGE
        )

        try:
            collector = WebCollector(raw_html=raw_html)
            items = collector.collect(req.target_url)
            return cls._process_collected_items(db, run, req, items, EvidenceType.PRODUCT_PAGE)
        except Exception as err:
            IngestionRunRepository.update_run_result(
                db=db,
                run=run,
                status=IngestionStatus.FAILED,
                error_message=str(err),
            )
            if isinstance(err, HTTPException):
                raise err
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Web Ingestion execution failed: {err}",
            )

    @classmethod
    def run_api_ingestion(
        cls, db: Session, req: APIIngestionRequest, raw_json: str | None = None
    ) -> IngestionRun:
        cls._validate_ingestion_target(db, req.company_id, req.problem_id, req.source_id)

        try:
            validate_safe_url(req.target_url)
        except UnsafeURLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security SSRF validation failed: {e}",
            )

        run = IngestionRunRepository.create(
            db=db, source_id=req.source_id, ingestion_type=IngestionType.API_JSON
        )

        try:
            collector = APICollector(raw_json=raw_json)
            items = collector.collect(req.target_url)
            return cls._process_collected_items(db, run, req, items, EvidenceType.OFFICIAL_DOC)
        except Exception as err:
            IngestionRunRepository.update_run_result(
                db=db,
                run=run,
                status=IngestionStatus.FAILED,
                error_message=str(err),
            )
            if isinstance(err, HTTPException):
                raise err
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API Ingestion execution failed: {err}",
            )

    @classmethod
    def _process_collected_items(
        cls,
        db: Session,
        run: IngestionRun,
        req: Any,
        items: list[CollectedItem],
        default_evidence_type: EvidenceType,
    ) -> IngestionRun:
        items_extracted = len(items)
        items_ingested = 0
        items_skipped = 0

        for item in items:
            if not item.content or not item.content.strip():
                items_skipped += 1
                continue

            content_hash = compute_content_hash(item.content)

            # Check database for existing evidence hash under (company_id, problem_id, content_hash)
            existing_stmt = select(EvidenceRecord).where(
                EvidenceRecord.company_id == req.company_id,
                EvidenceRecord.problem_id == req.problem_id,
                EvidenceRecord.content_hash == content_hash,
            )
            existing_record = db.execute(existing_stmt).scalar_one_or_none()

            if existing_record:
                items_skipped += 1
                continue

            evidence_record = EvidenceRecord(
                company_id=req.company_id,
                problem_id=req.problem_id,
                source_id=req.source_id,
                source_url=item.source_url or req.target_url,
                evidence_type=default_evidence_type,
                evidence_text=item.content,
                confidence_score=ConfidenceLevel.HIGH,
                content_hash=content_hash,
            )

            try:
                db.add(evidence_record)
                db.commit()
                items_ingested += 1
            except IntegrityError:
                db.rollback()
                items_skipped += 1

        return IngestionRunRepository.update_run_result(
            db=db,
            run=run,
            status=IngestionStatus.COMPLETED,
            items_extracted=items_extracted,
            items_ingested=items_ingested,
            items_skipped=items_skipped,
        )
