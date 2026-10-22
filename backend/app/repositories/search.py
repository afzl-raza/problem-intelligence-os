import re

from sqlalchemy import cast, func, or_, select, String, text
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.domain import Domain
from app.models.problem import Problem

_TOKEN = re.compile(r"[a-z0-9]+")

# Every distinct word (3+ chars) that appears in searchable text. Computed per
# request: fine at the current dataset size; materialize it if data grows large.
_CLOSEST_WORD_SQL = text(
    """
    WITH vocab AS (
        SELECT DISTINCT word FROM (
            SELECT regexp_split_to_table(
                lower(coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(category, '')),
                '[^a-z0-9]+') AS word FROM problems
            UNION ALL
            SELECT regexp_split_to_table(lower(coalesce(name, '') || ' ' || coalesce(industry, '')), '[^a-z0-9]+')
            FROM companies
            UNION ALL
            SELECT regexp_split_to_table(lower(name), '[^a-z0-9]+') FROM domains
        ) words
        WHERE length(word) >= 3
    )
    SELECT word FROM vocab
    WHERE word = :token OR similarity(word, :token) >= :min_similarity
    ORDER BY (word = :token) DESC, similarity(word, :token) DESC, word
    LIMIT 1
    """
)


def correct_query(db: Session, query: str, min_similarity: float = 0.4) -> str | None:
    """Replace each unknown word with the closest word in the searchable
    vocabulary. Returns None if nothing changed. Search operators (quotes,
    OR, -) are not preserved -- the correction is a plain-word suggestion."""
    tokens = _TOKEN.findall(query.lower())
    corrected = []
    for token in tokens:
        if len(token) < 3:
            corrected.append(token)
            continue
        closest = db.execute(
            _CLOSEST_WORD_SQL, {"token": token, "min_similarity": min_similarity}
        ).scalar()
        corrected.append(closest or token)
    return " ".join(corrected) if corrected != tokens else None


def suggest(db: Session, query: str, limit: int = 8, min_score: float = 0.5) -> list[dict]:
    """Typo-tolerant suggestions across problem titles, company names, and domain names.

    A candidate qualifies if it contains the query as a substring (autocomplete
    while typing) or its pg_trgm word_similarity clears `min_score` (typos like
    "parkng"). Substring matches rank first, then by similarity.
    """
    needle = query.strip().lower()
    sources = [
        ("problem", Problem.title, cast(Problem.id, String)),
        ("company", Company.name, cast(Company.id, String)),
        ("domain", Domain.name, Domain.slug),
    ]

    candidates: list[dict] = []
    for kind, label_col, value_col in sources:
        score = func.word_similarity(needle, func.lower(label_col))
        contains = func.strpos(func.lower(label_col), needle) > 0
        rows = db.execute(
            select(label_col, value_col, score, contains)
            .where(or_(contains, score >= min_score))
            .order_by(contains.desc(), score.desc(), label_col)
            .limit(limit)
        ).all()
        candidates.extend(
            {"kind": kind, "label": label, "value": value, "score": float(s), "_contains": bool(c)}
            for label, value, s, c in rows
        )

    candidates.sort(key=lambda c: (not c["_contains"], -c["score"], c["label"]))
    return [{k: v for k, v in c.items() if k != "_contains"} for c in candidates[:limit]]
