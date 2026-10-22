## Sprint 1.3 — Database Connection & Session Management

### Learned:
- SQLAlchemy Engine
- SQLAlchemy connection pooling
- SessionLocal / session factory
- FastAPI database dependency pattern
- Psycopg 3 PostgreSQL driver
- Database connection strings
- Environment-based database configuration
- Database connectivity testing

### Problems:
- SQLAlchemy was not initially installed.
- pydantic-settings was not installed.
- Python was executed from the wrong directory.
- SQLAlchemy initially attempted to use psycopg2 instead of psycopg 3.
- PostgreSQL connection initially appeared to hang during testing.

### Solved:
- Installed SQLAlchemy.
- Installed pydantic-settings.
- Corrected the working directory.
- Configured the database URL to use:
  postgresql+psycopg://
- Successfully connected SQLAlchemy to PostgreSQL running in Docker.
- Successfully executed SELECT 1 through both Engine and Session.

### Tests:
- Engine creation: PASSED
- PostgreSQL connectivity: PASSED
- SELECT 1: PASSED
- get_db() session: PASSED

### Next Steps:
- Complete Company CRUD (PATCH, DELETE).
- Add pagination & query filtering.
- Set up isolated test database and automated test suite.
- Add performance indexes via Alembic.

---

## Sprint 1.4 — Complete Company CRUD, Pagination, Filtering, Indexes & Test Isolation

### Learned:
- Strict 5-layer architecture enforcement (`API -> Service -> Repository -> SQLAlchemy -> PostgreSQL`).
- Clean pagination contracts using Pydantic response envelopes (`items`, `total`, `skip`, `limit`).
- Deterministic pagination ordering using `created_at DESC` with `id DESC` tie-breaker.
- FastAPI `Query` constraint validation (`skip >= 0`, `1 <= limit <= 100`).
- Test database isolation pattern (`problem_intelligence_test`) to prevent dev database contamination.
- Alembic autogeneration of B-tree indexes for standard query filters (`industry`, `country`, `funding_stage`).

### Problems:
- Pytest and HTTPX modules were missing from backend `.venv`.
- Python direct `pip.exe` invocation blocked by Windows App Control policy; solved via `python -m pip`.
- `datetime.utcnow()` deprecation warning in Python 3.12; solved by using timezone-aware `datetime.now(timezone.utc)`.

### Solved:
- Hardened `PATCH /companies/{company_id}` for partial updates and explicit `updated_at` timestamps.
- Implemented `DELETE /companies/{company_id}` returning `204 No Content` and handling non-existent records with `404 Not Found`.
- Updated `POST /companies` status code to `201 Created`.
- Upgraded `GET /companies` with pagination envelope schema (`CompanyPaginatedResponse`) and multi-criteria filters (`name`, `industry`, `country`, `funding_stage`).
- Created isolated test database `problem_intelligence_test` and fixtures in `conftest.py` ensuring table truncation between test cases.
- Implemented 13 unit & integration tests in `tests/test_companies.py` covering positive and negative paths (404s, 422s, invalid UUIDs, bad limits, negative skip).
- Generated Alembic migration `c626e2b11f88_add_company_indexes.py` and executed `alembic upgrade head` to index `industry`, `country`, and `funding_stage`.

### Tests:
- `test_create_company_success`: PASSED (201 Created)
- `test_get_company_by_id_success`: PASSED (200 OK)
- `test_get_company_not_found`: PASSED (404 Not Found)
- `test_get_company_invalid_uuid`: PASSED (422 Unprocessable Entity)
- `test_create_company_invalid_funding_stage`: PASSED (422 Unprocessable Entity)
- `test_list_companies_pagination_envelope`: PASSED (200 OK, envelope structure)
- `test_list_companies_filtering`: PASSED (200 OK, name/industry/country/funding_stage)
- `test_list_companies_invalid_limit`: PASSED (422 Unprocessable Entity)
- `test_list_companies_negative_skip`: PASSED (422 Unprocessable Entity)
- `test_patch_company_success`: PASSED (200 OK)
- `test_patch_company_not_found`: PASSED (404 Not Found)
- `test_delete_company_success`: PASSED (204 No Content -> 404 Not Found)
- `test_delete_company_not_found`: PASSED (404 Not Found)
- **Total Test Suite**: 13/13 PASSED (0.34s)

### Next Steps:
- Complete Problem Domain Foundation & Company-Problem relationship (Sprint 2.1).

---

## Sprint 2.1 — Problem Domain Foundation & Company-Problem Relationship

### Learned:
- Domain isolation by decoupling `Problem` entity (`app/models/problem.py`) from association entity (`app/models/company_problem.py`).
- JSON column storage for flexible tag representation (`domain_tags = Column(JSON, nullable=True)`).
- Domain enums for query safety: `ImpactLevel` enum (`low`, `medium`, `high`, `critical`, `unknown`) and `RelationshipType` enum (`primary_focus`, `secondary_feature`, `research_phase`, `deprecated`, `unknown`).
- Composite primary key pattern `(company_id, problem_id)` enforcing relationship uniqueness at the PostgreSQL database level.
- `ON DELETE CASCADE` behavior preventing orphaned association records when either a Company or Problem is removed.
- Multi-entity Pytest fixture isolation across `companies`, `problems`, and `company_problems` tables.

### Problems:
- Ensured relationship link parameters handle optional metadata defaults (`CompanyProblemLink` default payload).
- Standardized cascade deletion verification in automated tests to validate cleanup behavior.

### Solved:
- Created `Problem` SQLAlchemy model and `CompanyProblem` association model in separate module files.
- Generated Alembic migration `45f4b317ad94_create_problems_and_company_problems.py` and executed `alembic upgrade head`.
- Implemented `app/schemas/problem.py` featuring Pydantic schemas for `ProblemCreate`, `ProblemUpdate`, `ProblemResponse`, `ProblemPaginatedResponse`, `CompanyProblemLink`, and `CompanyProblemResponse`.
- Implemented `app/repositories/problem.py` and `app/services/problem.py` following strict 5-layer separation.
- Built FastAPI router in `app/api/problems.py` implementing Problem CRUD + `POST /problems/{problem_id}/companies/{company_id}`, `DELETE ...`, `GET /problems/{problem_id}/companies`, and `GET /companies/{company_id}/problems`.
- Updated test cleanup fixture in `tests/conftest.py` to truncate `companies, problems RESTART IDENTITY CASCADE`.
- Implemented 15 automated test cases in `tests/test_problems.py` covering Problem CRUD, pagination, filtering, company linking, unlinking, and cascade deletion.

### Tests:
- `test_create_problem_success`: PASSED (201 Created, JSON domain tags, ImpactLevel enum)
- `test_get_problem_by_id_success`: PASSED (200 OK)
- `test_get_problem_not_found`: PASSED (404 Not Found)
- `test_get_problem_invalid_uuid`: PASSED (422 Unprocessable Entity)
- `test_create_problem_invalid_impact_level`: PASSED (422 Unprocessable Entity)
- `test_list_problems_pagination_envelope`: PASSED (200 OK envelope)
- `test_list_problems_filtering`: PASSED (200 OK by title, category, impact_level)
- `test_patch_problem_success`: PASSED (200 OK)
- `test_delete_problem_success`: PASSED (204 No Content)
- `test_link_company_to_problem_success`: PASSED (201 Created)
- `test_unlink_company_from_problem_success`: PASSED (204 No Content)
- `test_cascade_delete_company_removes_link`: PASSED (Cascade cleanup)
- `test_cascade_delete_problem_removes_link`: PASSED (Cascade cleanup)
- **Total Test Suite (Companies + Problems)**: 26/26 PASSED (1.11s)

### Next Steps:
- Complete Evidence & Source Provenance Foundation (Sprint 2.2).

---

## Sprint 2.2 — Evidence & Source Provenance Foundation

### Learned:
- Provenance separation: `Source` entity (`app/models/source.py`) cataloging data origins decoupled from `EvidenceRecord` entity (`app/models/evidence.py`).
- Immutability principle for evidence records (`retrieved_at`, `created_at`, intentionally avoiding `updated_at` to preserve historical evidence integrity).
- Content hashing safeguard: `content_hash` (`VARCHAR(64)`) column for SHA-256 deduplication during future automated ingestion.
- Multi-enum categorization: `SourceType` (`company_website`, `news_article`, `academic_paper`, `code_repository`, `regulatory_filing`, `startup_database`, `social_media`, `job_posting`, `manual_entry`), `EvidenceType` (`official_doc`, `press_release`, `product_page`, `patent_filing`, `user_review`, `third_party_article`, `job_listing`, `unspecified`), and `ConfidenceLevel` (`high`, `medium`, `low`, `unverified`).
- Cascade integrity: `ON DELETE CASCADE` for company/problem entity deletions and `ON DELETE SET NULL` for source deletions.

### Problems:
- Preserved existing database indexes and ensured full test suite isolation when adding multi-table truncations in `conftest.py`.

### Solved:
- Created `Source` and `EvidenceRecord` models and registered them in `app/db/base.py`.
- Generated Alembic migration `b778d59966af_create_sources_and_evidence_records.py` and executed `alembic upgrade head`.
- Implemented Pydantic schemas in `app/schemas/source.py` and `app/schemas/evidence.py`.
- Built repositories (`app/repositories/source.py`, `app/repositories/evidence.py`) and services (`app/services/source.py`, `app/services/evidence.py`).
- Created FastAPI routers (`app/api/sources.py`, `app/api/evidence.py`) and registered them in `app/main.py`.
- Built key provenance endpoint: `GET /problems/{problem_id}/companies/{company_id}/evidence` returning verifiable proof items backing any company-problem link.
- Implemented 7 new automated tests in `tests/test_evidence.py` verifying Source CRUD, Evidence CRUD, link evidence queries, `SET NULL` source deletion, and `CASCADE` company deletion.

### Tests:
- `test_create_source_success`: PASSED (201 Created)
- `test_list_sources_pagination_filtering`: PASSED (200 OK by source_type & name)
- `test_create_evidence_success`: PASSED (201 Created with content_hash)
- `test_create_evidence_invalid_company_or_problem`: PASSED (404 Not Found)
- `test_get_evidence_for_link`: PASSED (200 OK — company-problem link provenance)
- `test_delete_source_sets_evidence_source_id_to_null`: PASSED (SET NULL cascade)
- `test_delete_company_cascades_and_removes_evidence`: PASSED (CASCADE cleanup)
- **Total Test Suite (Companies + Problems + Evidence)**: 33/33 PASSED (2.28s)

### Next Steps:
- Sprint 2.4 — Entity Resolution, Deduplication Pipeline & Search/Discovery Engine.

---

## Sprint 2.3 — Multi-Source Ingestion & Evidence Ingestion Foundation

### Learned:
- Pristine Base architecture: Model discovery for migrations performed in `alembic/env.py` without modifying `app/db/base.py`.
- Composite database unique constraints: Enforcing `uq_evidence_company_problem_hash` over `(company_id, problem_id, content_hash)` at PostgreSQL level.
- Service-level target validation: Explicitly verifying `CompanyProblem` link existence and optional `source_id` validity before `IngestionRun` record creation to return clean HTTP 404 responses instead of database foreign key errors.
- Security & SSRF Protection: Implementing DNS resolution checks blocking loopback (`127.0.0.1`, `localhost`), private IPv4 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and link-local IPs (`169.254.169.254`).
- Metric-rich job tracking: Tracking `items_extracted`, `items_ingested`, and `items_skipped` in `IngestionRun` model with `ON DELETE SET NULL` cascade behavior.

### Solved:
- Implemented `IngestionRun` model (`app/models/ingestion_run.py`) and generated Alembic migration `5ddb51966a53_create_ingestion_runs_and_evidence_unique_constraint.py`.
- Built SSRF security validator (`app/utils/security.py`) and centralized SHA-256 text normalizer (`app/utils/deduplication.py`).
- Implemented collector framework (`app/collectors/`) with `RSSCollector`, `WebCollector`, and `APICollector`.
- Created `IngestionService` (`app/services/ingestion.py`) validating company-problem link existence, validating optional cataloged `source_id`, extracting content, deduplicating via content hashes, and tracking run completion metrics.
- Built FastAPI router `app/api/ingestion.py` providing `POST /ingestion/rss`, `POST /ingestion/web`, `POST /ingestion/api`, `GET /ingestion/runs`, and `GET /ingestion/runs/{run_id}`.
- Added 11 automated integration tests in `tests/test_ingestion.py` covering RSS/Web/API parsing, SSRF security blocks, link & source validation, duplicate skipping, DB composite unique constraints, source deletion `SET NULL`, and run pagination.

### Tests:
- `test_validate_safe_url_ssrf_protection`: PASSED (Blocks loopback, private, link-local IPs)
- `test_rss_collector_ingestion_success`: PASSED (201 Created with metrics)
- `test_web_collector_ingestion_success`: PASSED (201 Created with metrics)
- `test_api_collector_ingestion_success`: PASSED (201 Created with metrics)
- `test_ssrf_endpoint_protection`: PASSED (400 Bad Request on internal IP requests)
- `test_ingestion_invalid_company_problem_link`: PASSED (404 Not Found on invalid link)
- `test_ingestion_invalid_source_id`: PASSED (404 Not Found on invalid source UUID)
- `test_ingestion_duplicate_skipping`: PASSED (Items ingested=0, items skipped=1 on duplicate run)
- `test_db_composite_unique_constraint`: PASSED (Database IntegrityError on duplicate insert)
- `test_source_deletion_sets_ingestion_run_source_id_to_null`: PASSED (SET NULL cascade)
- `test_list_ingestion_runs_pagination_filtering`: PASSED (200 OK envelope)
- **Total Test Suite (Companies + Problems + Evidence + Ingestion)**: 44/44 PASSED (3.99s)

### Next Steps:
- Complete Stage 5 (Sprint 2.4): Entity Resolution & Deduplication Pipeline.

---

## Sprint 2.4 — Company Entity Resolution & Deduplication

### Learned:
- Pushing duplicate-detection logic to the database layer (Postgres `pg_trgm` trigram similarity) rather than pulling rows into Python and fuzzy-matching in the app, consistent with this codebase's existing philosophy of DB-level integrity (composite unique constraints, B-tree indexes).
- Two-tier matching: a Python-side `normalize_company_name()` (lowercasing, punctuation stripping, repeated legal-suffix stripping — Inc, LLC, Ltd, Corp, Corporation, Co, GmbH, PBC, PLC) catches the common "same company, different legal suffix" case cheaply and exactly via an indexed `normalized_name` column, while a GIN trigram index on the raw `name` column catches everything else (typos, partial-name variants) via `pg_trgm`'s `similarity()` function.
- Migrations that need to run computed Python logic at backfill time (not just DDL) can import application code directly (`app.utils.entity_resolution.normalize_company_name`) inside the Alembic revision, following the same import pattern already used in `alembic/env.py`.
- Advisory-only design: duplicate detection never blocks `POST /companies` or auto-merges anything — it only surfaces ranked candidates via `GET /companies/resolve` for a human or future pipeline to act on, since a false-positive auto-merge would silently corrupt evidence/problem-link history.
- Merge correctness: reassigning a composite-PK association row (`CompanyProblem`, PK is `(company_id, problem_id)`) can collide if both companies are linked to the same problem. The surviving company's existing link is preserved as-is, the duplicate's conflicting link is left untouched, and `ON DELETE CASCADE` cleans it up automatically when the duplicate `Company` row is deleted — no explicit `db.delete()` needed for that row, which also avoids a false "expected to delete 1 row, 0 matched" SQLAlchemy warning from a redundant explicit delete racing the cascade.
- The isolated test database is built via `Base.metadata.create_all()` in `tests/conftest.py`, not via `alembic upgrade head` — so a new Postgres extension (`pg_trgm`) needed `CREATE EXTENSION IF NOT EXISTS` added directly to the test fixture, separately from the Alembic migration that enables it on the dev database.

### Problems:
- The autogenerated migration marked the new `normalized_name` column `NOT NULL` with no default, which would fail on any existing company rows; resolved by adding it nullable, backfilling via Python in the migration itself, then altering it to `NOT NULL`.
- `tests/test_company_resolution.py` initially failed on every `/companies/resolve` test with `UndefinedFunction: function similarity(...) does not exist` — the `pg_trgm` extension was enabled on the dev database by the migration but not on the test database, which bypasses Alembic entirely.
- The relationship-collision merge test produced a `SAWarning` ("DELETE statement ... expected to delete 1 row(s); 0 were matched") because an explicit `db.delete()` on the duplicate's conflicting `CompanyProblem` row raced the DB-level `ON DELETE CASCADE` triggered by deleting the duplicate `Company` row in the same transaction.

### Solved:
- Added Alembic migration `665a1bf5fb13_add_company_normalized_name_and_trgm_index` enabling `pg_trgm`, adding + backfilling `companies.normalized_name`, and creating both a standard B-tree index on it and a GIN trigram index (`gin_trgm_ops`) on `companies.name`.
- Implemented `app/utils/entity_resolution.py::normalize_company_name`.
- Implemented `app/repositories/company.py::find_similar_companies` (exact-normalized matches ranked first, then trigram matches above `min_similarity`, deduplicated by company id) and taught `create_company`/`update_company` to compute `normalized_name` automatically.
- Implemented `app/services/company.py::resolve_company_duplicates` and `merge_companies` (400 on self-merge, 404 on unknown ids, single-transaction reassignment of `EvidenceRecord.company_id` and non-colliding `CompanyProblem` links, collision-safe).
- Added `app/schemas/company.py::CompanyMatch`, `CompanyMergeRequest`, `CompanyMergeResponse` and two new endpoints in `app/api/companies.py`: `GET /companies/resolve`, `POST /companies/merge`.
- Fixed the test database by adding `CREATE EXTENSION IF NOT EXISTS pg_trgm` to `tests/conftest.py::setup_test_database`.
- Removed the redundant explicit `CompanyProblem` delete on the collision path in favor of relying on `ON DELETE CASCADE`.
- Added 8 new automated tests in `tests/test_company_resolution.py` covering exact-normalized matching, fuzzy matching above/below threshold, candidate deduplication, merge reassignment, merge relationship-collision handling, merge-not-found, and self-merge rejection.

### Tests:
- `test_resolve_exact_normalized_match`: PASSED (200 OK, score 1.0, `is_exact_match=True`)
- `test_resolve_fuzzy_match_above_threshold`: PASSED (200 OK, trigram match, `is_exact_match=False`)
- `test_resolve_fuzzy_match_below_threshold_excluded`: PASSED (200 OK, empty result for unrelated names)
- `test_resolve_deduplicates_candidates`: PASSED (company appears once despite matching both the exact and fuzzy paths)
- `test_merge_reassigns_evidence_and_problem_links`: PASSED (evidence + problem link moved to surviving company, duplicate deleted)
- `test_merge_preserves_keep_company_relationship_on_collision`: PASSED (surviving company's `relationship_type` untouched)
- `test_merge_not_found`: PASSED (404 Not Found)
- `test_merge_self_rejected`: PASSED (400 Bad Request)
- **Total Test Suite (Companies + Problems + Evidence + Ingestion + Company Resolution)**: 52/52 PASSED (5.64s)

### Next Steps:
- Stage 6: Search, Filtering & Similarity Engine (needed before a founder can find a `Problem` by natural-language description rather than exact `title`/`category` filters).

---

## Sprint 2.5 — Problem Full-Text Search

### Learned:
- Postgres `GENERATED ALWAYS AS ... STORED` columns can replace app-level sync code entirely for derived search data: `problems.search_vector` is a `tsvector` the database recomputes automatically on every insert/update, unlike Sprint 2.4's `normalized_name` which needed explicit Python computation in the repository on every write.
- Keeping a generated column's SQL expression as a single Python string constant (`PROBLEM_SEARCH_VECTOR_EXPRESSION` in `app/models/problem.py`), imported by both the SQLAlchemy model's `Computed(...)` and the Alembic migration's `sa.Computed(...)`, guarantees the model and the live DDL can never drift apart — same pattern as importing `normalize_company_name` into the Sprint 2.4 migration.
- `ts_rank()` weighting (`setweight()` with A/B/C/D) lets a single `tsvector` column encode field importance (title > description > category) without needing separate per-field search logic.
- Count/result parity matters for paginated full-text search exactly as much as for ordinary filtered lists: building the count query from the *same* base `select(...).where(...)` statement as the paginated query (rather than re-stating the match condition twice) is the only way to guarantee they can't drift apart, following the existing `get_problems`/`get_companies`/`get_evidences` pattern.
- FastAPI's own `Query(..., min_length=1, pattern=r"\S")` is enough to reject a blank or whitespace-only search query with a 422 before it ever reaches `plainto_tsquery` — no need for service-layer validation for this case.

### Problems:
- None blocking; the generated-column approach meant there was no equivalent to Sprint 2.4's "nullable backfill then alter to NOT NULL" dance, since existing `problems` rows get their `search_vector` computed automatically the moment the column is added.

### Solved:
- Added Alembic migration `2aba437f9b2a_add_problem_search_vector_and_gin_index`: a generated `search_vector` `TSVECTOR` column (title weight A, description weight B, category weight C) plus a GIN index, written manually (not autogenerated, same precedent as the Sprint 2.4 `pg_trgm` migration) since Alembic's autogenerate does not reliably detect generated-column expressions.
- Implemented `app/repositories/problem.py::search_problems` (ranked via `ts_rank`, `Problem.id.desc()` tie-breaker for deterministic pagination on tied scores, count query derived from the same base statement as the results).
- Implemented `app/services/problem.py::search_problems` wrapping the repository call into the standard `items`/`total`/`skip`/`limit` envelope.
- Added `app/schemas/problem.py::ProblemMatch` (full problem fields + `relevance_score`) and `ProblemSearchResponse`.
- Added `GET /problems/search` in `app/api/problems.py`, fully additive — the existing exact-filter `GET /problems` endpoint is untouched.
- Added 5 automated tests in `tests/test_problem_search.py` covering relevance ranking (title match outranks description-only match), no-match returning an empty paginated result (not an error), deterministic non-overlapping pagination, and 422 rejection of blank/whitespace-only queries.

### Tests:
- `test_search_ranks_title_match_above_description_match`: PASSED (title-weighted match ranks first)
- `test_search_no_matches_returns_empty_paginated_result`: PASSED (200 OK, empty `items`, `total=0`)
- `test_search_pagination`: PASSED (non-overlapping pages, full result set covered)
- `test_search_blank_query_rejected`: PASSED (422 Unprocessable Entity)
- `test_search_whitespace_query_rejected`: PASSED (422 Unprocessable Entity)
- **Total Test Suite (Companies + Problems + Evidence + Ingestion + Company Resolution + Problem Search)**: 57/57 PASSED (5.16s)

### Next Steps:
- Semantic/embeddings search as a Sprint 3+ addition (tied to the already-stubbed `OPENAI_API_KEY`; requires swapping the Postgres Docker image for a pgvector-enabled one).
- Stage 7: Opportunity Intelligence & Whitespace Signal Detection, built on top of this search layer.

---

## Sprint 3.0 — Demo Frontend (React + Vite)

### Why this sprint, now:
The project's own context/handoff doc (`problem_intelligence_os_project_context (1).docx`, snapshot 2026-08-27) states the real driving constraint: PIOS needs to be portfolio/interview-ready for campus recruiting within roughly 3-4 months, with "Phase 5 — Productization: frontend, authentication, deployment, monitoring, demo-ready flows" as that doc's own finish line. Confirmed with the user on 2026-10-23 that the deadline is still live with roughly 1-2 months of runway left. Everything through Sprint 2.5 was backend-only, reachable only via Swagger — this sprint makes the already-agreed MVP flow ("search a problem, see who's attacking it, see the evidence") actually visible and clickable.

### Learned:
- A generated-column-free schema still has real end-to-end verification burden: the three endpoints this frontend drives (`GET /problems/search`, `GET /problems/{problem_id}/companies`, `GET /problems/{problem_id}/companies/{company_id}/evidence`) needed their *exact* response shapes re-verified against live data before writing TypeScript types — one of them (`GET /problems/{problem_id}/companies`) has no `response_model` and returns a plain array of dicts, not a pagination envelope, which the frontend's types had to match exactly rather than assume.
- A real company plus a real homepage is not evidence that the company addresses a specific problem. Faithfully summarizing what a company's *official product page actually says* (checked via WebFetch during development, not recalled from memory) is the bar for demo evidence to be defensible rather than fabricated.
- The schema already had the right fields to distinguish illustrative seed data from verified research without inventing a new convention: `Source.is_verified=False` and `EvidenceRecord.confidence_score=ConfidenceLevel.UNVERIFIED`. The frontend surfaces this directly ("Unverified / illustrative" badge) rather than only encoding it in the database.
- An idempotent seed script is just "get-or-create everywhere, never truncate": exact `normalized_name` match for companies (reusing Sprint 2.4's `normalize_company_name`), exact `title` match for problems, exact `name` match for sources, the existing `link_company_to_problem` repository function (already upserts `CompanyProblem` links), and the same `(company_id, problem_id, content_hash)` existence check `IngestionService` already uses for evidence.
- CORS configured as explicit, least-privilege configuration (`CORS_ORIGINS` env var parsed into a list, `allow_methods=["GET"]`, `allow_credentials=False`, no wildcard) rather than a blanket `allow_origins=["*"]` workaround, since this demo frontend only ever reads.
- `GET /problems/{problem_id}/companies` returning 404 (problem doesn't exist) vs. `200` with an empty array (problem exists, no companies linked yet) are genuinely different states that needed distinct UI handling — collapsing them into one "no results" message would have hidden a real error.

### Problems:
- Vite's current `react-ts` template ships no default `src/vite-env.d.ts`; `import.meta.env.VITE_API_BASE_URL` needed an explicit `ImportMetaEnv` augmentation for it to type-check.
- The dev Postgres database already contained unrelated leftover rows from earlier manual testing (`"Test Startup"`, `"string"` — the literal Swagger UI placeholder value) that predate this sprint. Confirmed these are not duplicates produced by the seed script (verified by name and by re-running the script twice with a direct SQL row-count check) — left untouched, since the seed script must never clear data it doesn't own.

### Solved:
- Added `CORS_ORIGINS` to `Settings` (`app/core/config.py`) and `CORSMiddleware` to `app/main.py`.
- Scaffolded `frontend/` as a Vite `react-ts` app: typed API client (`src/api/client.ts`, `types.ts`, `fetchState.ts`), an orchestrator-only `App.tsx`, and four presentational components (`SearchBar`, `ProblemResults`, `CompanyList`, `EvidencePanel`) each owning their own loading/empty/error rendering.
- Built `backend/scripts/seed_demo_data.py`: four real, recognizable companies (Stripe, Linear, Plaid, Notion) linked to real-world problems they're known to address, with evidence text faithfully paraphrased from each company's actual official product page.
- Verified idempotency by running the seed script twice and cross-checking row counts directly in Postgres: second run created zero new companies/problems/sources/evidence records.
- Verified the full flow in an actual browser (Browser tool): search → ranked results → company panel (funding stage, relationship) → evidence panel (text + working source link + "Unverified / illustrative" badge) — plus the no-results, empty-query-disabled, and network-error states, by briefly stopping the backend mid-session.
- Confirmed `npm run build` (type-check + production bundle) succeeds cleanly.

### Tests:
- Backend regression: **57/57 PASSED** (unchanged — only additive CORS config, no endpoint logic touched).
- Frontend: `npx tsc -b` — PASSED (no type errors). `npm run build` — PASSED (225.92 kB JS bundle, gzip 70.56 kB).
- Manual browser verification (Browser tool, not automated): search with results, search with no results, empty-query button correctly disabled, network-failure error message, full search → company → evidence click-through with correct funding stage / relationship / evidence text / source link / unverified badge.
- Seed script idempotency: first run created 4 companies / 4 problems / 4 sources / 4 evidence records / 4 links; second run created 0 of each, confirmed via direct `SELECT count(*)` against the dev database.

### Next Steps:
- Stage 7: Opportunity Intelligence & Whitespace Signal Detection (deferred in favor of this sprint given the recruiting timeline).
- Semantic/embeddings search (Sprint 3+, tied to `OPENAI_API_KEY`).
- Data-entry forms, authentication, and deployment remain explicitly out of scope until a later Productization sprint.

---

## Sprint 3.1 — Generalized, Research-Driven Data Ingestion

### Why this sprint, now:
Feedback on the Sprint 3.0 demo: four hardcoded companies (Stripe/Linear/Plaid/Notion) didn't demonstrate the system handles an arbitrary problem domain — it only proved the plumbing works for one hand-picked set. The ask: cover a genuinely different domain (parking management SaaS, picked as the test case), with real companies fetched for real, not recalled from memory or invented, and without hardcoding a second one-off script for it.

### Learned:
- The fix for "don't hardcode" wasn't to avoid writing data down — real evidence has to live somewhere. It was to separate the *data* (one JSON file per researched domain) from the *mechanism* (one domain-agnostic idempotent loader), so a new domain is "do the research, write a JSON file" rather than "write a new Python script."
- WebSearch is necessary but not sufficient for finding genuinely verifiable companies: an initial broad search ("parking management SaaS companies") surfaced mostly SEO/affiliate directory content (Capterra listings, vendor blogs) for small, thinly-documented players. Targeted follow-up searches for specific, well-known companies (Metropolis, ParkMobile, Passport, T2 Systems) found verifiable official sites with substantive content to faithfully summarize. Broad-then-narrow was the working pattern, not one search.
- The same WebFetch-then-faithfully-paraphrase discipline from Sprint 3.0 generalizes cleanly to a new domain: one source (Passport's fact-sheet PDF) didn't yield readable text, so that source was swapped for the company's actual homepage rather than filled in from assumption.
- `impact_level` is an inherently qualitative/judgment field (unlike evidence_text, which must be a faithful quote/paraphrase) — assigning it per researched problem is a defensible editorial judgment, not a fabricated fact, as long as it's not presented as sourced from the page itself.

### Problems:
- The old `seed_demo_data.py` had the exact four companies, their fields, and their evidence text written directly into Python source — functionally hardcoded even though the content itself was real. Running it again, or extending it, meant editing code.

### Solved:
- Extracted `scripts/_ingestion_lib.py`: the get-or-create-everywhere, never-truncate logic from Sprint 3.0's seed script, now domain-agnostic (takes plain dicts, not a fixed company list).
- Replaced `seed_demo_data.py` with `scripts/ingest_research_data.py`, which takes one or more JSON file paths on the command line and contains zero company/problem data itself.
- Moved the Sprint 3.0 dataset to `scripts/research_data/founding_demo.json` unchanged (still real, still idempotent — re-ran it through the new loader and confirmed it still returns "reused" for every entity).
- Researched a second, independent domain for real: used `WebSearch` to identify real parking-management companies, then `WebFetch` against each company's own official site (metropolis.io, parkmobile.io, passportinc.com, t2systems.com) to extract faithful, grounded evidence text — written to `scripts/research_data/parking_management_saas.json`, with the research method itself recorded in the file.
- Ingested both datasets, then re-ran the parking dataset a second time and confirmed via a direct `SELECT count(*)` against Postgres that zero new rows were created (same idempotency guarantee as Sprint 3.0, now proven to hold for a dataset the loader had never seen before this sprint).
- Verified the frontend picks up the new domain with zero frontend changes: searching "parking management" in the running demo returns all 4 real parking companies, ranked, with working source links back to their real homepages and the same "Unverified / illustrative" honesty badge.

### Tests:
- Backend regression: **57/57 PASSED** (no application code changed, only `backend/scripts/`).
- Ingestion idempotency: first run on `parking_management_saas.json` created 4 companies / 4 problems / 4 sources / 4 evidence records; second run created 0 of each. Direct Postgres row counts confirmed no duplicates across both datasets combined (11 companies — 7 pre-existing/unrelated + 4 new — 8 problems, 9 sources, 8 evidence records, 8 links).
- Manual browser verification: `GET /problems/search?q=parking` and the live frontend both return all 4 new real companies with correct relevance ranking; clicking through to T2 Systems' evidence panel shows the correct faithful evidence text and a working `https://www.t2systems.com/` source link.

### Next Steps:
- Adding more research-data domains is now just "research it for real, write a JSON file" — no code changes required.
- A live, on-demand research/discovery feature (user types any topic, the backend performs web research automatically) remains a distinct, much larger decision — new paid search/LLM API infrastructure, anti-hallucination grounding at request time, async job handling — not undertaken in this sprint.

---

## Sprint 3.2 — Domains + Search Foundation (2026-10-23)

### Why this sprint, now:
First sprint of the expansion roadmap (3.2 → 4.0). A status review against the project context doc showed search was bottlenecked by data *structure*, not algorithms: the research domain ("Parking Management SaaS") was never persisted (`domain_tags` null everywhere), free-text categories already disagreed with each other, and companies had no real search. User-confirmed order: domains + search foundation first, then a landscape view (3.3), semantic search with a local model (3.4), whitespace signals (3.5), and an in-app research pipeline with a human review queue (4.0).

### Learned:
- `websearch_to_tsquery` gives users `"phrases"`, `OR`, and `-exclusion` for free; plain multi-word queries behave exactly as `plainto_tsquery` did, so every existing search test passed unchanged.
- Phrase search is strict about adjacency: `"curb enforcement"` does not match "Curb **and parking** enforcement". That's correct behavior, but test fixtures have to use genuinely adjacent phrases.
- `ts_headline` accepts control characters as `StartSel`/`StopSel` when passed as a bound parameter. Using `\u0002`/`\u0003` sentinels means the API never emits HTML and the frontend builds `<mark>` elements itself, so highlighting can't become an XSS vector. `HighlightAll=true` keeps short descriptions whole instead of truncating them mid-sentence.
- An entity-level "did you mean" is the wrong tool for a misspelled *query*: suggesting the domain "Parking Management SaaS" for `parkng` leads to a search for "saas", which no problem text contains, so it comes back empty again. A token-level spellcheck against the real searchable vocabulary (`parkng managment` → `parking management`), returned only when the corrected query actually has results, is what the UX needs.
- `pg_trgm` thresholds had to be set from data, not guessed. Real typos scored 0.50–0.64 `similarity` (`parkng`, `managment`, `enforcment`); unrelated words ≤0.17. In suggestions, false positives (`park` → "Passport") sat at exactly 0.40 `word_similarity` and real ones at 0.57+, so suggest uses 0.5 and spellcheck 0.4. Transposition typos (`payemnt`, 0.33) are a known miss.
- Companies with sparse profiles (researched entries carry only name + industry) are nearly invisible to profile-only search. Matching a company *through its linked problems*, ranked by the better of the two scores, is what "who works on X" actually means.
- File-watching reload (`uvicorn --reload`) didn't fire reliably in this OneDrive-synced folder, so explicit restarts are the dependable path when smoke-testing.

### Problems:
- The founding dataset wasn't one domain; its file-level "domain" label was really a dataset name. The JSON format now separates `dataset` (label) from `default_domains`, with a per-entry `domains` override.
- Research ingestion lived in `scripts/` with no automated tests, and Sprint 4.0's approval step will need the same logic.
- `make test` and the README ran only `test_companies.py` (13 of the then-57 tests).
- Both result lists and both selection panels could show stale data if an earlier slow request resolved after a newer one.

### Solved:
- Migration `ee5da04ca95e`: `domains` (unique slug), `problem_domains` (many-to-many, cascade both sides, mirroring `company_problems`), and a generated `companies.search_vector` with a GIN index, using the same single-source expression-constant pattern as problems.
- Moved ingestion to `app/services/research_ingestion.py` (domain-aware; the CLI is now a thin wrapper). Re-running both datasets backfilled 4 domains on the first run and created zero rows on the second; Postgres confirms 8 problems ↔ 8 domain links.
- `GET /problems/search` gained filters, facets (counted over the text match *before* filters so chips keep their counts), per-item domains, and sentinel snippets. Added `GET /companies/search`, `GET /domains`, `GET /domains/{slug}`, `GET /search/suggest`, and `GET /search/spellcheck`.
- Frontend: filter chips with counts, highlighted snippets (`Highlighted` component, no `dangerouslySetInnerHTML`), debounced keyboard-navigable autocomplete (ARIA combobox), "Did you mean…?", a Companies tab, and request-sequence guards against stale responses.
- Fixed the test commands in the README and Makefile to run the whole suite.

### Tests:
- Backend: **79/79 PASSED** (57 existing + 22 new: `test_research_ingestion.py`, `test_domains.py`, `test_company_search.py`, `test_search_suggest.py`, and extended `test_problem_search.py`).
- Frontend: `tsc -b` clean, `oxlint` clean (two intentional control-character regexes suppressed with a reason), `npm run build` passes.
- Browser (real dev DB): autocomplete for `park`; `parking` → 4 results with highlighted matches and Domain/Impact chips; the **high** filter narrows to 2 while other facet counts stay visible; the Companies tab shows the 4 parking companies with site links; `parkng managment` → "Did you mean parking management?" → clicking reruns the corrected search; problem → Passport → evidence click-through still works; no console errors.

### Next Steps:
- Sprint 3.3: `GET /domains/{slug}/landscape`, a multi-page frontend with `react-router-dom` (domain browse, landscape, problem and company pages), and 2–3 more real researched domains.

