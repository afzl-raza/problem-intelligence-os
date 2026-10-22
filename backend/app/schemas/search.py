from typing import Literal

from pydantic import BaseModel, Field


class SpellcheckResponse(BaseModel):
    query: str
    corrected: str | None = Field(description="Corrected query, only set when it differs and returns at least one problem")


class Suggestion(BaseModel):
    kind: Literal["problem", "company", "domain"]
    label: str
    value: str = Field(description="Problem/company UUID, or domain slug for kind='domain'")
    score: float
