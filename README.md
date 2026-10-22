# Problem Intelligence OS (PIOS)

**Problem Intelligence OS** is a global problem-intelligence platform designed for developers, students, founders, startups, and researchers.

Instead of serving as a static directory of startups, PIOS provides a dynamic intelligence layer that helps users uncover:
- What related work already exists for a discovered problem.
- Which companies and projects are actively working on adjacent problems.
- The maturity level and funding stage of current solutions.
- Whitespace and opportunity gaps remaining in the market.

---

## Technical Architecture

PIOS is engineered with a strict 5-layer separation of concerns:
`API Router → Service Layer → Repository Layer → SQLAlchemy ORM → PostgreSQL Database`.

### Current Tech Stack
- **Backend Framework**: FastAPI 0.141.1 (Python 3.12.5)
- **ASGI Server**: Uvicorn 0.52.1
- **Database**: PostgreSQL 16.14 (Dockerized)
- **ORM & Driver**: SQLAlchemy 2.0.51 + Psycopg 3.3.4
- **Schema Management & Migrations**: Alembic 1.19.0
- **Validation**: Pydantic 2.13.4
- **Test Automation**: Pytest 9.1.1 + HTTPX 0.28.1

---

## Quick Start

### 1. Database Setup (Docker)
Ensure Docker is running, then start PostgreSQL:
```bash
docker compose up -d
```

### 2. Virtual Environment & Migrations
```bash
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
```

### 3. Run FastAPI Development Server
```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Interactive documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Run Automated Test Suite
Tests run on an isolated test database (`problem_intelligence_test`):
```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

### 5. Ingest Research Data (optional)
Populates real companies/problems/evidence for the demo frontend from `backend/scripts/research_data/*.json` (safe to run repeatedly — idempotent, never clears data). No company/problem data is hardcoded in the script itself — each JSON file is a real research pass (WebSearch to find real companies, WebFetch against each one's own official page to extract faithful evidence), and covering a new domain means adding a new JSON file, not writing new code:
```bash
cd backend
.venv\Scripts\python.exe scripts\ingest_research_data.py scripts\research_data\founding_demo.json
.venv\Scripts\python.exe scripts\ingest_research_data.py scripts\research_data\parking_management_saas.json
```

### 6. Run the Demo Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) with the backend running — search a problem, see who's attacking it, click through to the evidence behind the claim.

---

## Documentation
- [Architecture Specifications](architecture.md)
- [API Endpoints Documentation](api.md)
- [Database Schema & Migration Guide](database.md)
- [Engineering Log](Engineering_Log.md)
- [Project Roadmap](roadmap.md)