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

### Company ↔ Problem Relationships
| Method | Endpoint | Status Code | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/problems/{problem_id}/companies/{company_id}` | `201 Created` | Link a company to a problem with metadata |
| `DELETE` | `/problems/{problem_id}/companies/{company_id}` | `204 No Content` | Unlink a company from a problem |
| `GET` | `/problems/{problem_id}/companies` | `200 OK` | Get all companies attempting to solve a problem |
| `GET` | `/companies/{company_id}/problems` | `200 OK` | Get all problems addressed by a specific company |

---

## Endpoint Response Envelopes

### `GET /problems`
Query Parameters: `skip` (min 0), `limit` (1-100), `title`, `category`, `impact_level` enum (`low`, `medium`, `high`, `critical`, `unknown`).

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "Cross-Border Payment Settlement Latency",
      "description": "B2B payment processing delays in LatAm region.",
      "category": "FinTech",
      "domain_tags": ["fintech", "payments", "latam"],
      "impact_level": "high",
      "created_at": "2026-08-28T00:18:12.689639Z",
      "updated_at": "2026-08-28T00:18:12.689639Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

## Interactive Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`
