import math

import pytest

from app.core.config import settings
from app.services import embeddings
from app.services.embeddings import (
    EMBEDDING_DIMENSIONS,
    FixedEmbedder,
    HashingEmbedder,
    embed_query_cached,
    get_embedder,
    set_embedder_override,
)


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def test_hashing_embedder_is_deterministic_unit_length_and_right_size():
    embedder = HashingEmbedder()
    first = embedder.embed_query("manual checkout friction")

    assert first == embedder.embed_query("manual checkout friction")
    assert len(first) == EMBEDDING_DIMENSIONS == embedder.dimensions
    assert math.isclose(math.sqrt(sum(v * v for v in first)), 1.0, rel_tol=1e-9)
    assert embedder.embed_documents(["manual checkout friction"])[0] == first


def test_hashing_embedder_places_texts_sharing_words_closer():
    embedder = HashingEmbedder()
    query, near, far = embedder.embed_documents(
        ["checkout friction at exit", "manual checkout friction", "bank account connectivity"]
    )

    assert cosine(query, near) > cosine(query, far)


def test_fixed_embedder_returns_the_vectors_it_was_given_padded_and_normalized():
    embedder = FixedEmbedder({"a": [3.0, 4.0]})

    vector = embedder.embed_query("a")

    assert vector[:2] == [0.6, 0.8]
    assert len(vector) == EMBEDDING_DIMENSIONS and set(vector[2:]) == {0.0}


def test_get_embedder_honours_override_and_disabled_provider(monkeypatch):
    assert get_embedder().name == "hashing-test"  # the autouse test fixture

    set_embedder_override(None)  # explicit "semantic disabled"
    assert get_embedder() is None

    set_embedder_override(None, active=False)  # no override: fall back to settings
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "none")
    assert get_embedder() is None


class CountingEmbedder(HashingEmbedder):
    name = "counting-test"

    def __init__(self):
        super().__init__()
        self.query_calls = 0

    def embed_query(self, text):
        self.query_calls += 1
        return super().embed_query(text)


def test_query_embeddings_are_cached_per_embedder_and_text():
    embedder = CountingEmbedder()

    for _ in range(3):
        embed_query_cached(embedder, "slow checkout")
    embed_query_cached(embedder, "something else")

    assert embedder.query_calls == 2


@pytest.mark.model
def test_real_local_model_embeds_by_meaning():
    """Runs the real fastembed model (downloads ~130MB on first use). `pytest -m model`."""
    real = embeddings.FastEmbedEmbedder(settings.EMBEDDING_MODEL, settings.EMBEDDING_CACHE_DIR)

    query = real.embed_query("slow checkout at the exit gate")
    related, unrelated = real.embed_documents(
        ["Manual checkout friction at parking facilities", "Fragmented bank account connectivity for fintech apps"]
    )

    assert len(query) == real.dimensions == EMBEDDING_DIMENSIONS
    assert cosine(query, related) > cosine(query, unrelated)
