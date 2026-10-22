from typing import Annotated

from fastapi import Query

# PostgreSQL text cannot contain NUL (\x00), so letting one reach a query
# surfaces as a database error (HTTP 500) instead of a clean 422. These types
# reject it at the API boundary. Note `\S` alone would not do: NUL is not
# whitespace, so the non-whitespace character is required to be non-NUL too.

# Free-text search: needs at least one non-whitespace character.
SearchQuery = Annotated[
    str,
    Query(
        min_length=1,
        max_length=200,
        pattern=r"^[^\x00]*[^\x00\s][^\x00]*$",
        description='Search query (supports "phrases", OR, -exclusion)',
    ),
]

# For optional filter values (domain slug, category, name, ...): any non-empty text without NUL.
NO_NUL_PATTERN = r"^[^\x00]+$"
