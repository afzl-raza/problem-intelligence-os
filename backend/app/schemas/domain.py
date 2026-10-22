from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DomainResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    created_at: datetime
    problem_count: int
    company_count: int
