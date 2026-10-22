# Problem Intelligence OS — API Specification

## Base URL
`http://127.0.0.1:8000`

---

## Endpoints Summary

### Companies
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/companies` | `201 Created` | Register a new company entity |
| `GET` | `/companies` | `200 OK` | List companies with pagination & filtering |
| `GET` | `/companies/{company_id}` | `200 OK` | Retrieve single company details |
| `PATCH` | `/companies/{company_id}` | `200 OK` | Partially update an existing company |
| `DELETE` | `/companies/{company_id}` | `204 No Content` | Delete a company record |

### Problems
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/problems` | `201 Created` | Register a new problem entity |
| `GET` | `/problems` | `200 OK` | List problems with pagination & filtering |
| `GET` | `/problems/{problem_id}` | `200 OK` | Retrieve single problem details |
| `PATCH` | `/problems/{problem_id}` | `200 OK` | Partially update an existing problem |
| `DELETE` | `/problems/{problem_id}` | `204 No Content` | Delete a problem record |
| `GET` | `/problems/search` | `200 OK` | Ranked full-text search over problem title/description/category. Web-search syntax (`"phrase"`, `OR`, `-exclude`); filters `domain` (slug), `category`, `impact_level`, `funding_stage`; returns domain/impact `facets` (counted before filters), per-item `domains`, and a highlighted `snippet` (matches wrapped in `\u0002`…`\u0003`, never HTML) |

### Company ↔ Problem Relationships
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/problems/{problem_id}/companies/{company_id}` | `201 Created` | Link a company to a problem with metadata |
| `DELETE` | `/problems/{problem_id}/companies/{company_id}` | `204 No Content` | Unlink a company from a problem |
| `GET` | `/problems/{problem_id}/companies` | `200 OK` | Get all companies attempting to solve a problem |
| `GET` | `/companies/{company_id}/problems` | `200 OK` | Get all problems addressed by a specific company |

### Domains
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/domains` | `200 OK` | All problem domains (e.g. `parking-management-saas`) with problem and distinct-company counts |
| `GET` | `/domains/{slug}` | `200 OK` / `404` | A single domain with its counts |

### Search
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/companies/search` | `200 OK` | Ranked full-text company search; a company matches on its own profile **or** through any problem it is linked to. Optional `funding_stage` filter |
| `GET` | `/search/suggest` | `200 OK` | Autocomplete / typo-tolerant suggestions across problem titles, company names, and domain names (`pg_trgm` word similarity) |
| `GET` | `/search/spellcheck` | `200 OK` | "Did you mean" correction against the searchable vocabulary; `corrected` is only set when it differs **and** returns at least one problem |

### Company Entity Resolution & Deduplication
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/companies/resolve` | `200 OK` | Find likely duplicate companies for a candidate name (exact normalized match + Postgres trigram fuzzy match); advisory only |
| `POST` | `/companies/merge` | `200 OK` | Merge a duplicate company into another: reassigns evidence & problem links, deletes the duplicate (transactional) |

### Data Sources
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/sources` | `201 Created` | Register a new data source catalog entry |
| `GET` | `/sources` | `200 OK` | List data sources with pagination & filtering |
| `GET` | `/sources/{source_id}` | `200 OK` | Retrieve details for a specific data source |
| `PATCH` | `/sources/{source_id}` | `200 OK` | Update metadata for a data source |
| `DELETE` | `/sources/{source_id}` | `204 No Content` | Delete a data source (sets `source_id` to NULL in evidence) |

### Evidence & Provenance
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/evidence` | `201 Created` | Record verifiable evidence for a company-problem link |
| `GET` | `/evidence` | `200 OK` | List evidence records with pagination & filters |
| `GET` | `/evidence/{evidence_id}` | `200 OK` | Retrieve single evidence record details |
| `PATCH` | `/evidence/{evidence_id}` | `200 OK` | Update an evidence record |
| `DELETE` | `/evidence/{evidence_id}` | `204 No Content` | Delete an evidence record |
| `GET` | `/problems/{problem_id}/companies/{company_id}/evidence` | `200 OK` | Get all supporting evidence records for a company-problem link |

### Multi-Source Ingestion
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/ingestion/rss` | `201 Created` | Trigger RSS/Atom XML feed fetch, parse, deduplicate & store evidence |
| `POST` | `/ingestion/web` | `201 Created` | Trigger Web HTML document scrape, extract main text, deduplicate & store evidence |
| `POST` | `/ingestion/api` | `201 Created` | Trigger JSON REST API feed parse, deduplicate & store evidence |
| `GET` | `/ingestion/runs` | `200 OK` | List ingestion job runs with pagination & filtering (`source_id`, `status`, `ingestion_type`) |
| `GET` | `/ingestion/runs/{run_id}` | `200 OK` | Retrieve detailed execution metrics and audit details for a run |

---

## Cross-Origin Access
`CORS_ORIGINS` (env var, comma-separated) controls which frontend origins may call this API. Local dev default: `http://localhost:5173,http://127.0.0.1:5173` (the Vite dev server). Only `GET` is allowed cross-origin — the demo frontend is read-only.

## Demo Frontend
A read-only React + Vite SPA (`frontend/`) consumes the search, suggest, spellcheck, company-search, and company/evidence endpoints to drive a search → companies → evidence click-through flow with filters, highlighting, and autocomplete. See the root `README.md` for setup, and `backend/scripts/ingest_research_data.py` for idempotent research data.

---

## Interactive Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`
