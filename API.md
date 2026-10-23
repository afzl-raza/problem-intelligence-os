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
| `GET` | `/problems/search` | `200 OK` | Ranked full-text search over problem title/description/category. Web-search syntax (`"phrase"`, `OR`, `-exclude`); filters `domain` (slug), `category`, `impact_level`, `funding_stage`; returns `facets` for domain, category, impact level, and company funding stage (distinct-problem counts over the text match, computed before filters), per-item `domains`, and highlighted `title_snippet` / `snippet` (matches wrapped in `\u0002`…`\u0003`, never HTML) Add `mode=hybrid` to also match by meaning: keyword and semantic candidates (top 50 each; semantic needs cosine similarity >= `SEMANTIC_MIN_SIMILARITY`, default 0.60) are merged with Reciprocal Rank Fusion, so every keyword hit is kept. Each item then carries `match_type` (`keyword` / `semantic` / `both`) and `similarity`; the response carries `mode_used` and, when a hybrid request fell back to keyword results (provider off, nothing indexed, model unavailable), a `semantic_note`. Default `mode=keyword` is unchanged; filters and facets work identically in both modes. |

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
| `GET` | `/domains/{slug}/landscape` | `200 OK` / `404` | Everything the domain page needs: counts (same source as `/domains`), category / impact / funding distributions, distinct companies (with problems-in-domain), and a paginated problem list (`category`, `impact_level`, `skip`, `limit`) with `company_count`, `evidence_count`, `verified_evidence_count`. Raw counts only — no "gap" labels |

### Entity detail pages
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/problems/{problem_id}/detail` | `200 OK` / `404` | Problem + domains + every linked company, each with its evidence items, source record, and `verification_status` |
| `GET` | `/companies/{company_id}/detail` | `200 OK` / `404` | Company + every linked problem (with domains), each with evidence items, source record, and `verification_status` |

`verification_status` is `verified` only when the evidence has a cataloged source, that source is `is_verified`, and `confidence_score` is not `unverified`; otherwise `unverified`. The rule lives in one place (`app/services/evidence.py::is_verified_evidence`) and the UI renders it verbatim.

### Search
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/companies/search` | `200 OK` | Ranked full-text company search; a company matches on its own profile **or** through any problem it is linked to. Optional `funding_stage` filter |
| `GET` | `/search/suggest` | `200 OK` | Autocomplete / typo-tolerant suggestions across problem titles, company names, and domain names (`pg_trgm` word similarity) |
| `GET` | `/problems/{problem_id}/related` | `200 OK` / `404` | Problems closest in meaning to this one (cosine similarity at or above `RELATED_MIN_SIMILARITY`, default 0.70), excluding itself, best first; `limit` 1-20. `semantic_available=false` with no items when meaning-based search is off or the problem isn't indexed. Similarity is a relevance signal, not proof of equivalence |
| `GET` | `/search/semantic/status` | `200 OK` | Whether meaning-based search can answer now, the model name and dimensions, thresholds, and how many problems are indexed / stale (`stale` is null while the provider is disabled) |
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

## Input Validation
- Search queries (`q` on `/problems/search`, `/companies/search`, `/search/suggest`, `/search/spellcheck`) must contain at least one non-whitespace character, no NUL bytes, and at most 200 characters; otherwise `422`.
- Optional text filters (`domain`, `category`, `name`, `industry`, `country`, `title`, source `name`) reject NUL bytes with `422`. PostgreSQL text cannot hold `\x00`, so without this check it would surface as a `500`.
- A value the database itself refuses on create/update (a NUL byte in a JSON body, text longer than its column) is mapped to `422` by an app-level handler; the driver's error text is not echoed.
- Odd-but-legal queries (punctuation only, unbalanced quotes, bare `OR`/`-`, emoji, SQL-looking text) return `200`, usually with no results.

## Cross-Origin Access
`CORS_ORIGINS` (env var, comma-separated) controls which frontend origins may call this API. Local dev default: `http://localhost:5173,http://127.0.0.1:5173` (the Vite dev server). Only `GET` is allowed cross-origin — the demo frontend is read-only.

## Demo Frontend
A read-only React + Vite SPA (`frontend/`) consumes the search, suggest, spellcheck, company-search, and company/evidence endpoints to drive a search → companies → evidence click-through flow with filters, highlighting, and autocomplete. See the root `README.md` for setup, and `backend/scripts/ingest_research_data.py` for idempotent research data.

---

## Interactive Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`
