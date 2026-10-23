"""Embedding boundary for semantic search.

Everything that needs vectors goes through the `Embedder` protocol, so the
real local model (`FastEmbedEmbedder`) can be swapped for deterministic fakes
in tests -- the test suite never downloads or runs a model.

Embedding a *document* only ever happens in the indexing command
(`app.services.embedding_index`), never inside ordinary request handling. The
one thing embedded at request time is the user's *query*, and only for
`mode=hybrid` searches.
"""
import hashlib
import math
import os
import re
import threading
from importlib.metadata import version
from typing import Protocol

from app.core.config import settings
from app.models.problem_embedding import EMBEDDING_DIMENSIONS

# huggingface_hub warns about symlinks on every download on Windows without Developer Mode; caching still works.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


class EmbeddingUnavailable(Exception):
    """The configured embedder cannot produce vectors right now (disabled, model missing, ...)."""


class Embedder(Protocol):
    name: str
    dimensions: int
    library_version: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    """Local ONNX embedding model via fastembed. The model loads lazily on first
    use (and is downloaded once into `cache_dir`); load failures surface as
    `EmbeddingUnavailable` so callers can fall back to keyword search."""

    def __init__(self, model_name: str, cache_dir: str):
        self.name = model_name
        self.dimensions = EMBEDDING_DIMENSIONS
        self.library_version = version("fastembed")
        self._cache_dir = cache_dir
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                try:
                    from fastembed import TextEmbedding

                    self._model = TextEmbedding(model_name=self.name, cache_dir=self._cache_dir)
                except Exception as error:
                    raise EmbeddingUnavailable(f"could not load embedding model '{self.name}': {error}") from error
            return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        return [vector.tolist() for vector in model.passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        model = self._load()
        return next(iter(model.query_embed([text]))).tolist()


_TOKEN = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    """Deterministic test embedder: hashes word tokens into a unit vector, so texts
    sharing words are closer. Not semantic -- it exists to make tests reproducible."""

    name = "hashing-test"
    library_version = "test"

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.md5(token.rstrip("s").encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class FixedEmbedder:
    """Test embedder with hand-set vectors for exact ranking assertions. Vectors are
    short lists, zero-padded to `dimensions`; embedding unknown text is a test bug."""

    name = "fixed-test"
    library_version = "test"

    def __init__(self, vectors: dict[str, list[float]], dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions
        self._vectors = {text: self._pad(v) for text, v in vectors.items()}

    def _pad(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector] + [0.0] * (self.dimensions - len(vector))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors[t] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectors[text]


_override: Embedder | None = None
_override_set = False
_default: Embedder | None = None
_query_cache: dict[tuple[int, str], list[float]] = {}
_QUERY_CACHE_LIMIT = 256


def set_embedder_override(embedder: Embedder | None, *, active: bool = True) -> None:
    """Install (or clear) a process-wide embedder, bypassing settings. Used by tests."""
    global _override, _override_set
    _override, _override_set = embedder, active
    _query_cache.clear()


def get_embedder() -> Embedder | None:
    """The configured embedder, or None when semantic search is disabled."""
    global _default
    if _override_set:
        return _override
    if settings.EMBEDDING_PROVIDER == "none":
        return None
    if _default is None:
        _default = FastEmbedEmbedder(settings.EMBEDDING_MODEL, settings.EMBEDDING_CACHE_DIR)
    return _default


def embed_query_cached(embedder: Embedder, text: str) -> list[float]:
    """Query embeddings are cached so load-more and filter clicks don't re-embed."""
    key = (id(embedder), text)
    if key not in _query_cache:
        if len(_query_cache) >= _QUERY_CACHE_LIMIT:
            _query_cache.pop(next(iter(_query_cache)))
        _query_cache[key] = embedder.embed_query(text)
    return _query_cache[key]
