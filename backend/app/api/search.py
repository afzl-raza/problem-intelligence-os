from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import SpellcheckResponse, Suggestion
from app.services.search import spellcheck, suggest

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get(
    "/suggest",
    response_model=list[Suggestion],
    summary="Typo-tolerant suggestions",
    description=(
        "Autocomplete and 'did you mean' suggestions across problem titles, "
        "company names, and domain names, using pg_trgm word similarity."
    ),
)
def suggest_endpoint(
    q: str = Query(..., min_length=1, max_length=200, pattern=r"\S", description="Partial or misspelled query"),
    limit: int = Query(8, ge=1, le=20, description="Maximum suggestions to return"),
    db: Session = Depends(get_db),
):
    return suggest(db=db, query=q, limit=limit)


@router.get(
    "/spellcheck",
    response_model=SpellcheckResponse,
    summary="'Did you mean' query correction",
    description=(
        "Corrects misspelled words against the vocabulary of problem, company, "
        "and domain text. Only returns a correction that yields at least one problem."
    ),
)
def spellcheck_endpoint(
    q: str = Query(..., min_length=1, max_length=200, pattern=r"\S", description="Query to check"),
    db: Session = Depends(get_db),
):
    return spellcheck(db=db, query=q)
