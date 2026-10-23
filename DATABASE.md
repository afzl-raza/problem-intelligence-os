# Problem Intelligence OS — Database Architecture & Schema

## Database Connection Details

- **Database Engine**: PostgreSQL 16.14
- **Dev Database Name**: `problem_intelligence`
- **Test Database Name**: `problem_intelligence_test`
- **ORM**: SQLAlchemy 2.0.51
- **Driver**: Psycopg 3.3.4 (`postgresql+psycopg://`)
- **Extensions**: `pg_trgm` (trigram similarity, enabled by migration `665a1bf5fb13`; powers company duplicate detection)
- **Full-Text Search**: native Postgres `tsvector`/`ts_rank`/`websearch_to_tsquery`/`ts_headline` (no extension required); problems since migration `2aba437f9b2a`, companies since `ee5da04ca95e`
- **Vector search**: `pgvector` 0.8 (`vector` extension, migration `cf8128f756de`). The database image is built from `docker/postgres/Dockerfile` (`postgres:16` + `postgresql-16-pgvector`) rather than switching to `pgvector/pgvector`, whose older Debian base (glibc 2.36 vs the volume's 2.41) would have put text-index collation at risk. Tests create the extension in `problem_intelligence_test` themselves.
- **Typo tolerance**: `pg_trgm` `word_similarity`/`similarity` power `/search/suggest` and `/search/spellcheck`

---

## Migration History

Managed strictly via Alembic (`backend/alembic`).

| Revision ID | Description | Created | Status |
| :--- | :--- | :--- | :--- |
| `f30d45993e91` | `create_companies_table` | Sprint 1.3 | Applied |
| `c626e2b11f88` | `add_company_indexes` | Sprint 1.4 | Applied |
| `45f4b317ad94` | `create_problems_and_company_problems` | Sprint 2.1 | Applied |
| `b778d59966af` | `create_sources_and_evidence_records` | Sprint 2.2 | Applied |
| `5ddb51966a53` | `create_ingestion_runs_and_evidence_unique_constraint` | Sprint 2.3 | Applied |
| `665a1bf5fb13` | `add_company_normalized_name_and_trgm_index` | Sprint 2.4 | Applied |
| `2aba437f9b2a` | `add_problem_search_vector_and_gin_index` | Sprint 2.5 | Applied |
| `ee5da04ca95e` | `add_domains_and_company_search_vector` | Sprint 3.2 | Applied |
| `cf8128f756de` | `add_problem_embeddings_and_pgvector` | Sprint 3.4 | Applied |

---

## Tables

### 1. `companies` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique identifier |
| `name` | `VARCHAR(255)` | NOT NULL | `ix_companies_name`, `ix_companies_name_trgm` (GIN, `gin_trgm_ops`) | Entity primary name |
| `normalized_name` | `VARCHAR(255)` | NOT NULL | `ix_companies_normalized_name` | Lowercased, punctuation-stripped, legal-suffix-stripped name used for exact duplicate detection |
| `industry` | `VARCHAR(100)` | NULLABLE | `ix_companies_industry` | Primary industry domain |
| `country` | `VARCHAR(100)` | NULLABLE | `ix_companies_country` | Country location |
| `funding_stage` | `VARCHAR/ENUM` | NOT NULL, default `unknown` | `ix_companies_funding_stage` | Categorical funding stage |
| `search_vector` | `TSVECTOR` | GENERATED ALWAYS AS ... STORED (name A, industry B, description C, problem_summary C) | `ix_companies_search_vector` (GIN) | Full-text search vector, maintained by Postgres |

---

### 2. `problems` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique problem identifier |
| `title` | `VARCHAR(255)` | NOT NULL | `ix_problems_title` | Short title of problem |
| `category` | `VARCHAR(100)` | NULLABLE | `ix_problems_category` | Category taxonomy |
| `domain_tags` | `JSON` | NULLABLE | No | Tag array |
| `impact_level` | `VARCHAR/ENUM` | NOT NULL, default `unknown` | `ix_problems_impact_level` | Categorical severity |
| `search_vector` | `TSVECTOR` | GENERATED ALWAYS AS ... STORED (title weight A, description weight B, category weight C) | `ix_problems_search_vector` (GIN) | Full-text search vector, maintained automatically by Postgres |

---

### 3. `company_problems` Junction Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `company_id` | `UUID` | PK, FK -> `companies.id` ON DELETE CASCADE | Composite PK | Foreign key to company |
| `problem_id` | `UUID` | PK, FK -> `problems.id` ON DELETE CASCADE | Composite PK | Foreign key to problem |
| `relationship_type` | `VARCHAR/ENUM` | NOT NULL, default `primary_focus` | `ix_company_problems_relationship_type` | Relation type |

---

### 4. `sources` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique identifier for data source |
| `name` | `VARCHAR(255)` | NOT NULL | `ix_sources_name` | Human-readable source name |
| `source_type` | `VARCHAR/ENUM` | NOT NULL, default `manual_entry` | `ix_sources_source_type` | Source type taxonomy (`company_website`, `news_article`, `academic_paper`, `code_repository`, `regulatory_filing`, `startup_database`, `social_media`, `job_posting`, `manual_entry`) |
| `base_url` | `VARCHAR(500)` | NULLABLE | No | Domain base URL |
| `is_verified` | `BOOLEAN` | NOT NULL, default `True` | No | Source verification flag |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record creation timestamp |

---

### 5. `evidence_records` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique identifier for evidence record |
| `company_id` | `UUID` | FK -> `companies.id` ON DELETE CASCADE | `ix_evidence_records_company_id` | Foreign key to company |
| `problem_id` | `UUID` | FK -> `problems.id` ON DELETE CASCADE | `ix_evidence_records_problem_id` | Foreign key to problem |
| `source_id` | `UUID` | FK -> `sources.id` ON DELETE SET NULL | `ix_evidence_records_source_id` | Foreign key to cataloged source |
| `source_url` | `VARCHAR(1000)`| NULLABLE | No | Exact URL where evidence was fetched |
| `evidence_type` | `VARCHAR/ENUM` | NOT NULL, default `official_doc` | `ix_evidence_records_evidence_type` | Evidence type (`official_doc`, `press_release`, `product_page`, `patent_filing`, `user_review`, `third_party_article`, `job_listing`, `unspecified`) |
| `evidence_text` | `TEXT` | NOT NULL | No | Exact raw snippet supporting claim |
| `confidence_score` | `VARCHAR/ENUM` | NOT NULL, default `high` | `ix_evidence_records_confidence_score` | Confidence level (`high`, `medium`, `low`, `unverified`) |
| `content_hash` | `VARCHAR(64)` | NULLABLE | `ix_evidence_records_content_hash` | SHA-256 hash for deduplication |
| `retrieved_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | UTC timestamp when evidence was fetched |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record creation timestamp |

*Note*: Table includes composite unique constraint `uq_evidence_company_problem_hash` over `(company_id, problem_id, content_hash)`.

---

### 6. `ingestion_runs` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique identifier for ingestion job run |
| `source_id` | `UUID` | FK -> `sources.id` ON DELETE SET NULL | `ix_ingestion_runs_source_id` | Foreign key to target cataloged data source |
| `status` | `VARCHAR/ENUM` | NOT NULL, default `pending` | `ix_ingestion_runs_status` | Job execution status (`pending`, `running`, `completed`, `failed`) |
| `ingestion_type` | `VARCHAR/ENUM` | NOT NULL, default `manual` | `ix_ingestion_runs_ingestion_type` | Ingestion source channel (`rss`, `web_page`, `api_json`, `manual`) |
| `items_extracted` | `INTEGER` | NOT NULL, default `0` | No | Count of raw items extracted from target source |
| `items_ingested` | `INTEGER` | NOT NULL, default `0` | No | Count of new evidence records successfully stored |
| `items_skipped` | `INTEGER` | NOT NULL, default `0` | No | Count of duplicate/invalid items skipped |
| `error_message` | `TEXT` | NULLABLE | No | Detailed exception message if run failed |
| `started_at` | `TIMESTAMPTZ` | NULLABLE | No | Timestamp when collector execution began |
| `completed_at` | `TIMESTAMPTZ` | NULLABLE | No | Timestamp when job completed or failed |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | `ix_ingestion_runs_created_at` | Record creation timestamp |

---

### 7. `domains` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique domain identifier |
| `slug` | `VARCHAR(120)` | NOT NULL, UNIQUE | `ix_domains_slug` (unique) | URL-safe key, e.g. `parking-management-saas` |
| `name` | `VARCHAR(255)` | NOT NULL | No | Display name, e.g. `Parking Management SaaS` |
| `description` | `TEXT` | NULLABLE | No | Optional description |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record creation timestamp |

---

### 8. `problem_domains` Junction Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `problem_id` | `UUID` | PK, FK -> `problems.id` ON DELETE CASCADE | Composite PK | Problem in the domain |
| `domain_id` | `UUID` | PK, FK -> `domains.id` ON DELETE CASCADE | Composite PK, `ix_problem_domains_domain_id` | Domain the problem belongs to |

*Note*: Many-to-many — a problem can span domains. Companies belong to domains transitively through their linked problems (no direct company↔domain table, so there is a single source of truth).

---

### 9. `problem_embeddings` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `problem_id` | `UUID` | PK, FK -> `problems.id` ON DELETE CASCADE | Primary key | The problem this vector represents (one row per problem) |
| `embedding` | `vector(384)` | NOT NULL | `ix_problem_embeddings_embedding_hnsw` (HNSW, `vector_cosine_ops`) | Embedding of the problem's title, description, and category |
| `model_name` | `VARCHAR(120)` | NOT NULL | No | Model that produced the vector, e.g. `BAAI/bge-small-en-v1.5` |
| `model_dimensions` | `INTEGER` | NOT NULL | No | Vector size at the time of embedding |
| `library_version` | `VARCHAR(50)` | NOT NULL | No | Embedding library version (`fastembed`) |
| `source_hash` | `VARCHAR(64)` | NOT NULL | No | Content hash of the embedded text; a mismatch with the current text means the vector is stale |
| `embedded_at` | `TIMESTAMPTZ` | NOT NULL | No | When the vector was computed |

*Notes*: kept apart from `problems` so ordinary problem queries never load vectors and a model change is a re-index, not a `problems` schema change. A vector is **stale** when it is missing, its `source_hash` differs from the current text, or its `model_name` / `model_dimensions` differ from the configured embedder. Vectors are written only by `scripts/embed_problems.py`, never by API requests.
