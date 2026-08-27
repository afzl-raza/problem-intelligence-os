# Problem Intelligence OS — Database Architecture & Schema

## Database Connection Details

- **Database Engine**: PostgreSQL 16.14
- **Dev Database Name**: `problem_intelligence`
- **Test Database Name**: `problem_intelligence_test`
- **ORM**: SQLAlchemy 2.0.51
- **Driver**: Psycopg 3.3.4 (`postgresql+psycopg://`)

---

## Migration History

Managed strictly via Alembic (`backend/alembic`).

| Revision ID | Description | Created | Status |
| :--- | :--- | :--- | :--- |
| `f30d45993e91` | `create_companies_table` | Sprint 1.3 | Applied |
| `c626e2b11f88` | `add_company_indexes` | Sprint 1.4 | Applied |
| `45f4b317ad94` | `create_problems_and_company_problems` | Sprint 2.1 | Applied |

---

## Tables

### 1. `companies` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique identifier |
| `name` | `VARCHAR(255)` | NOT NULL | `ix_companies_name` | Entity primary name |
| `legal_name` | `VARCHAR(255)` | NULLABLE | No | Legal registered name |
| `description` | `TEXT` | NULLABLE | No | Company description |
| `website_url` | `VARCHAR(500)` | NULLABLE | No | Primary website |
| `linkedin_url` | `VARCHAR(500)` | NULLABLE | No | LinkedIn profile URL |
| `problem_summary` | `TEXT` | NULLABLE | No | Summary of problem solved |
| `industry` | `VARCHAR(100)` | NULLABLE | `ix_companies_industry` | Primary industry domain |
| `country` | `VARCHAR(100)` | NULLABLE | `ix_companies_country` | Country location |
| `city` | `VARCHAR(100)` | NULLABLE | No | City location |
| `founded_year` | `INTEGER` | NULLABLE | No | Year founded |
| `funding_stage` | `VARCHAR/ENUM` | NOT NULL, default `unknown` | `ix_companies_funding_stage` | Categorical funding stage |
| `contact_email` | `VARCHAR(320)` | NULLABLE | No | Business email |
| `contact_phone` | `VARCHAR(50)` | NULLABLE | No | Public phone number |
| `source` | `VARCHAR(100)` | NULLABLE | No | Initial discovery source |
| `source_url` | `VARCHAR(500)` | NULLABLE | No | Provenance URL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record update timestamp |

---

### 2. `problems` Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, `uuid4` default | Yes | Unique problem identifier |
| `title` | `VARCHAR(255)` | NOT NULL | `ix_problems_title` | Short title of problem |
| `description` | `TEXT` | NULLABLE | No | Detailed problem statement |
| `category` | `VARCHAR(100)` | NULLABLE | `ix_problems_category` | Category taxonomy |
| `domain_tags` | `JSON` | NULLABLE | No | Tag array (e.g. `["fintech", "latam"]`) |
| `impact_level` | `VARCHAR/ENUM` | NOT NULL, default `unknown` | `ix_problems_impact_level` | Categorical severity (`low`, `medium`, `high`, `critical`, `unknown`) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Record update timestamp |

---

### 3. `company_problems` Junction Table

| Column Name | Data Type | Constraints | Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `company_id` | `UUID` | PK, FK -> `companies.id` ON DELETE CASCADE | Composite PK | Foreign key to company |
| `problem_id` | `UUID` | PK, FK -> `problems.id` ON DELETE CASCADE | Composite PK | Foreign key to problem |
| `relationship_type` | `VARCHAR/ENUM` | NOT NULL, default `primary_focus` | `ix_company_problems_relationship_type` | Relation type (`primary_focus`, `secondary_feature`, `research_phase`, `deprecated`, `unknown`) |
| `evidence_summary` | `TEXT` | NULLABLE | No | Summary of rationale/evidence |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, UTC default | No | Link creation timestamp |
