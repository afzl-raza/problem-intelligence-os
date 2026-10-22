import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Lowercase, collapse every run of non-alphanumerics into a single hyphen, trim hyphens."""
    return _NON_ALNUM.sub("-", text.strip().lower()).strip("-")
