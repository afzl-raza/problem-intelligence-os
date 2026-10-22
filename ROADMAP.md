# Problem Intelligence OS — Roadmap

## Strategic Evolution

```text
Stage 1: Startup & Company Discovery (COMPLETE — Sprint 1.4)
Stage 2: Problem Entity & Company-Problem Link Layer (COMPLETE — Sprint 2.1)
Stage 3: Evidence & Source Provenance Layer (COMPLETE — Sprint 2.2)
Stage 4: Multi-Source Ingestion & Evidence Ingestion Foundation (IN PROGRESS — Sprint 2.3 COMPLETE)
Stage 5: Entity Resolution & Deduplication Pipeline (NEXT — Sprint 2.4)
Stage 6: Search, Filtering & Similarity Engine
Stage 7: Opportunity Intelligence & Whitespace Signal Detection
Stage 8: Global Platform & Interactive UI Dashboard
```

---

## Phase Breakdown

### Phase 1: Backend & Domain Foundation (Sprints 1.1 – 1.4) [DONE]
- [x] Docker PostgreSQL 16.14 setup
- [x] FastAPI, Pydantic, SQLAlchemy 2.0, Psycopg 3 setup
- [x] Alembic migration engine configuration
- [x] Company domain model & FundingStage enum
- [x] Production-grade Company CRUD (POST 201, GET 200, PATCH 200, DELETE 204)
- [x] Response envelope pagination (`items`, `total`, `skip`, `limit`)
- [x] Query search & filtering (`name`, `industry`, `country`, `funding_stage`)
- [x] B-tree indexing for search performance
- [x] Isolated test database (`problem_intelligence_test`) & Pytest suite (13/13 passing)

### Phase 2: Problem Domain & Relationships (Sprint 2.1) [DONE]
- [x] `Problem` entity model (`app/models/problem.py`) with `ImpactLevel` enum & `JSON` domain tags
- [x] `CompanyProblem` association entity model (`app/models/company_problem.py`) with `RelationshipType` enum & composite primary key
- [x] Alembic migration `45f4b317ad94_create_problems_and_company_problems`
- [x] `Problem` CRUD endpoints (`POST 201`, `GET 200` paginated, `GET 200` by ID, `PATCH 200`, `DELETE 204`)
- [x] Bi-directional association endpoints (`POST`, `DELETE`, `GET`)

### Phase 3: Evidence & Source Provenance Foundation (Sprint 2.2) [DONE]
- [x] `Source` catalog entity model (`app/models/source.py`) with `SourceType` enum & verification flag
- [x] `EvidenceRecord` entity model (`app/models/evidence.py`) with `EvidenceType`, `ConfidenceLevel` enums, raw `evidence_text`, and SHA-256 `content_hash`
- [x] Foreign key integrity (`ON DELETE CASCADE` for companies/problems, `ON DELETE SET NULL` for sources)
- [x] Alembic migration `b778d59966af_create_sources_and_evidence_records` applied to PostgreSQL
- [x] Pydantic schemas, repositories, services, and FastAPI routers (`app/api/sources.py`, `app/api/evidence.py`)
- [x] Provenance API: `GET /problems/{problem_id}/companies/{company_id}/evidence`
- [x] Automated test suite in `tests/test_evidence.py` (33/33 total tests passing)

### Phase 4: Multi-Source Ingestion & Evidence Ingestion Foundation (Sprint 2.3) [DONE]
- [x] `IngestionRun` tracking entity model (`app/models/ingestion_run.py`) with `IngestionStatus` & `IngestionType` enums
- [x] Database-level composite unique constraint `uq_evidence_company_problem_hash` on `(company_id, problem_id, content_hash)`
- [x] Alembic migration `5ddb51966a53_create_ingestion_runs_and_evidence_unique_constraint` applied
- [x] SSRF security validator (`app/utils/security.py`) blocking private, loopback, and link-local IP addresses
- [x] Centralized SHA-256 text normalization & content hashing engine (`app/utils/deduplication.py`)
- [x] Collector engine (`app/collectors/`) supporting RSS/Atom feeds, Web HTML pages, and REST API JSON feeds
- [x] Service layer validation checking `CompanyProblem` link existence before evidence ingestion
- [x] FastAPI ingestion endpoints: `POST /ingestion/rss`, `POST /ingestion/web`, `POST /ingestion/api`, `GET /ingestion/runs`, `GET /ingestion/runs/{run_id}`
- [x] Automated test suite in `tests/test_ingestion.py` (43/43 total tests passing)

### Phase 5: Entity Resolution & Deduplication Pipeline (Sprint 2.4) [NEXT]
- [ ] Cross-source entity resolution & company name fuzzy matching
- [ ] Vector & keyword search engine integration
- [ ] Whitespace opportunity signal detection
