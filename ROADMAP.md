# Problem Intelligence OS — Roadmap

## Strategic Evolution

```text
Stage 1: Startup & Company Discovery (COMPLETE — Sprint 1.4)
Stage 2: Problem Entity & Company-Problem Link Layer (COMPLETE — Sprint 2.1)
Stage 3: Evidence & Source Provenance Layer (COMPLETE — Sprint 2.2)
Stage 4: Multi-Source Ingestion & Evidence Ingestion Foundation (COMPLETE — Sprint 2.3)
Stage 5: Entity Resolution & Deduplication Pipeline (COMPLETE — Sprint 2.4)
Stage 6: Search, Filtering & Similarity Engine (IN PROGRESS — keyword search complete through Sprint 3.2; semantic search next)
Stage 7: Opportunity Intelligence & Whitespace Signal Detection
Stage 8: Global Platform & Interactive UI Dashboard (STARTED — Sprint 3.0: demo frontend)
```

Note: campus-recruiting timeline pressure (see `Engineering_Log.md`'s Sprint 3.0 entry) moved the first slice of Stage 8 ahead of Stage 7 — a working, clickable frontend was judged more important to have sooner than whitespace detection, which remains open.

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

### Phase 5: Entity Resolution & Deduplication Pipeline (Sprint 2.4) [DONE]
- [x] Cross-source entity resolution & company name fuzzy matching
  - [x] `normalized_name` column + legal-suffix/punctuation normalization (`app/utils/entity_resolution.py`)
  - [x] Postgres `pg_trgm` trigram similarity matching (`app/repositories/company.py::find_similar_companies`)
  - [x] Advisory duplicate-candidate endpoint: `GET /companies/resolve`
  - [x] Transactional merge endpoint: `POST /companies/merge` (reassigns evidence & problem links, preserves existing relationships on collision)

### Phase 6: Search, Filtering & Similarity Engine (Sprint 2.5) [IN PROGRESS]
- [x] Keyword/full-text search over problems
  - [x] Generated `TSVECTOR` column on `problems` (title weight A, description weight B, category weight C), maintained automatically by Postgres
  - [x] GIN index for fast `@@` lookups
  - [x] Ranked search endpoint: `GET /problems/search?q=...` (`ts_rank`, paginated, additive to the existing exact-filter `GET /problems`)
- [x] **Sprint 3.2 — Domains + search foundation**
  - [x] `domains` + `problem_domains` tables; research data now persists its domain (backfilled for both datasets)
  - [x] Ingestion moved in-app (`app/services/research_ingestion.py`) and covered by automated tests
  - [x] Web-search syntax (`"phrases"`, `OR`, `-exclude`), filters (domain, category, impact, funding stage), facet counts, XSS-safe highlighted snippets
  - [x] Company full-text search, matching on own profile or linked problems (`GET /companies/search`)
  - [x] Typo-tolerant autocomplete (`GET /search/suggest`) and "did you mean" (`GET /search/spellcheck`)
  - [x] Frontend: filter chips, highlighting, autocomplete, "did you mean", Companies tab
- [ ] Semantic/embeddings search — Sprint 3.4, local open-source model (decided 2026-10-23)
- [ ] Whitespace opportunity signal detection — Sprint 3.5

### Phase 7: Demo Frontend (Sprint 3.0) [DONE] — first slice of Stage 8
- [x] React + Vite + TypeScript SPA (`frontend/`), read-only, no router: search → companies → evidence
- [x] `CORS_ORIGINS` config + `CORSMiddleware` (GET-only, explicit origins, no wildcard)
- [x] Typed API client against the real response schemas, with explicit loading/empty/error states
- [x] Idempotent, domain-agnostic research-ingestion tool (`backend/scripts/ingest_research_data.py` + `scripts/research_data/*.json`): real companies found via WebSearch, evidence faithfully paraphrased from each company's own official page via WebFetch, `is_verified=False` / `confidence_score=unverified` to flag illustrative data. Two datasets shipped: the founding demo (Stripe/Linear/Plaid/Notion) and Parking Management SaaS (Metropolis, ParkMobile, Passport, T2 Systems). Covering a new domain is "add a JSON file," not "write new code."
- [ ] Data-entry forms, authentication, deployment, dashboards — explicitly out of scope for this sprint
