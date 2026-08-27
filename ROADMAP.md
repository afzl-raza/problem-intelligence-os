# Problem Intelligence OS — Roadmap

## Strategic Evolution

```text
Stage 1: Startup & Company Discovery (COMPLETE — Sprint 1.4)
Stage 2: Problem Entity & Company-Problem Link Layer (COMPLETE — Sprint 2.1)
Stage 3: Multi-Source Ingestion & Evidence Provenance Layer (NEXT — Sprint 2.2)
Stage 4: Entity Resolution & Deduplication Pipeline
Stage 5: Search, Filtering & Similarity Engine
Stage 6: Opportunity Intelligence & Whitespace Signal Detection
Stage 7: Global Platform & Interactive UI Dashboard
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

### Phase 2: Problem Domain Foundation & Relationships (Sprint 2.1) [DONE]
- [x] `Problem` entity model (`app/models/problem.py`) with `ImpactLevel` enum & `JSON` domain tags
- [x] `CompanyProblem` association entity model (`app/models/company_problem.py`) with `RelationshipType` enum & composite primary key
- [x] Alembic migration `45f4b317ad94_create_problems_and_company_problems`
- [x] `Problem` CRUD endpoints (`POST 201`, `GET 200` paginated, `GET 200` by ID, `PATCH 200`, `DELETE 204`)
- [x] Bi-directional association endpoints:
  - `POST /problems/{problem_id}/companies/{company_id}` (201 Created)
  - `DELETE /problems/{problem_id}/companies/{company_id}` (204 No Content)
  - `GET /problems/{problem_id}/companies` (200 OK)
  - `GET /companies/{company_id}/problems` (200 OK)
- [x] Pytest suite in `tests/test_problems.py` (26/26 total tests passing)

### Phase 3: Evidence & Provenance Ingestion (Sprints 2.2 – 3.3) [NEXT]
- [ ] Multi-source evidence model (`Source`, `EvidenceRecord`)
- [ ] Confidence scoring & extraction schema
- [ ] Data normalization & entity resolution pipeline
