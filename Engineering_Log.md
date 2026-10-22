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

