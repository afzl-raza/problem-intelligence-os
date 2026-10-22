import re

# Common legal suffixes that don't change company identity, longest-first
# so "corporation" is stripped before a shorter overlapping token could match.
_LEGAL_SUFFIXES = [
    "incorporated",
    "corporation",
    "company",
    "limited",
    "gmbh",
    "inc",
    "llc",
    "ltd",
    "corp",
    "co",
    "pbc",
    "plc",
]

_SUFFIX_PATTERN = re.compile(
    r"\b(?:" + "|".join(_LEGAL_SUFFIXES) + r")\.?\s*$"
)
_PUNCTUATION_PATTERN = re.compile(r"[^\w\s]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_company_name(name: str) -> str:
    """Normalize a company name for duplicate detection by lowercasing,
    stripping punctuation, collapsing whitespace, and repeatedly removing
    trailing legal-entity suffixes (Inc, LLC, Ltd, Corp, Co, GmbH, PBC, PLC, ...)."""
    if not name:
        return ""

    cleaned = _PUNCTUATION_PATTERN.sub(" ", name.strip().lower())
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()

    while True:
        stripped = _SUFFIX_PATTERN.sub("", cleaned).strip()
        if stripped == cleaned:
            break
        cleaned = stripped

    return cleaned
