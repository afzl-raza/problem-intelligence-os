from sqlalchemy.orm import Session

from app.repositories.problem import count_problem_matches
from app.repositories.search import correct_query, suggest as suggest_repository


def suggest(db: Session, query: str, limit: int = 8) -> list[dict]:
    return suggest_repository(db=db, query=query, limit=limit)


def spellcheck(db: Session, query: str) -> dict:
    """Offer a corrected query only if it would actually return problems --
    never suggest a 'did you mean' that also comes back empty."""
    corrected = correct_query(db=db, query=query)
    if corrected is None or count_problem_matches(db=db, query=corrected) == 0:
        corrected = None
    return {"query": query, "corrected": corrected}
