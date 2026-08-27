# Problem Intelligence OS (PIOS) — Architectural Overview

## Architectural Philosophy

PIOS is built using a strict 5-layer separation of concerns:

```text
API Router Layer (FastAPI)
         ↓
  Service Layer (Business Logic)
         ↓
 Repository Layer (Database Access)
         ↓
   SQLAlchemy (ORM Domain Mapping)
         ↓
  PostgreSQL (Relational Storage)
```

### Layer Descriptions

1. **API Router Layer (`app/api/`)**: Handles HTTP concerns, route definitions, Query parameter extraction, and status codes (200, 201, 204, 404, 422).
2. **Service Layer (`app/services/`)**: Encapsulates core domain business logic, data transformation, and orchestration between repositories and external services.
3. **Repository Layer (`app/repositories/`)**: Encapsulates all SQLAlchemy queries, database session calls, filtering logic, and pagination envelope assembly.
4. **SQLAlchemy ORM (`app/models/` & `app/db/`)**: Defines database entity models (`Company`, etc.), column mappings, relationships, and engine/session management.
5. **Database / PostgreSQL**: Relational foundation running in Docker (`problem_intelligence` for development/production and `problem_intelligence_test` for isolated automated test runs).

---

## Technical Stack

- **Language**: Python 3.12.5
- **Web Framework**: FastAPI 0.141.1
- **ASGI Server**: Uvicorn 0.52.1
- **Validation**: Pydantic 2.13.4 + pydantic-settings 2.15.0
- **ORM**: SQLAlchemy 2.0.51
- **DB Driver**: Psycopg 3.3.4
- **Database**: PostgreSQL 16.14 (Docker)
- **Migrations**: Alembic 1.19.0
- **Testing**: Pytest 9.1.1 + HTTPX 0.28.1
