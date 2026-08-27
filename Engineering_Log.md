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
- Phase 2.2 — Evidence & Provenance Model (`EvidenceRecord`, source tracking, confidence levels).
- Phase 2.3 — Problem Extraction & Structuring Schema.
