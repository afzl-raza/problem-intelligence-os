import hashlib
import re


def normalize_text(text: str) -> str:
    """Normalize text by stripping leading/trailing whitespace, normalizing line endings and internal spacing, and lowercasing for canonical SHA-256 content hashing."""
    if not text:
        return ""
    
    # Replace multiple whitespaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned.lower()


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of normalized text snippet."""
    canonical = normalize_text(text)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
