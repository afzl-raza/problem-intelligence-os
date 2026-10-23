import pytest
from sqlalchemy import func, select

from app.models.problem import Problem
from app.models.problem_embedding import ProblemEmbedding
from app.services.embedding_index import embedding_source_text, find_stale, reindex, status
from app.services.embeddings import FixedEmbedder, HashingEmbedder
from app.services.research_ingestion import ingest_dataset
from factories import make_entry


class OtherModel(HashingEmbedder):
    name = "other-model-test"


def seed(db_session, count=3):
    ingest_dataset(db_session, {"entries": [make_entry(f"Co {i}", f"Problem number {i}") for i in range(count)]})


def embedded_count(db_session):
    return db_session.scalar(select(func.count()).select_from(ProblemEmbedding))


def test_reindex_embeds_everything_and_records_model_details(db_session):
    seed(db_session)

    report = reindex(db_session, HashingEmbedder())

    assert report == {"total": 3, "embedded": 3, "already_current": 0}
    row = db_session.scalars(select(ProblemEmbedding)).first()
    assert (row.model_name, row.model_dimensions, row.library_version) == ("hashing-test", 384, "test")
    assert len(row.source_hash) == 64 and row.embedded_at is not None


def test_second_run_embeds_nothing(db_session):
    seed(db_session)
    embedder = HashingEmbedder()
    reindex(db_session, embedder)

    assert reindex(db_session, embedder) == {"total": 3, "embedded": 0, "already_current": 3}


def test_force_reembeds_everything(db_session):
    seed(db_session)
    reindex(db_session, HashingEmbedder())

    assert reindex(db_session, HashingEmbedder(), force=True)["embedded"] == 3


def test_changing_problem_text_makes_only_that_problem_stale(db_session):
    seed(db_session)
    embedder = HashingEmbedder()
    reindex(db_session, embedder)
    problem = db_session.scalars(select(Problem).where(Problem.title == "Problem number 1")).one()

    problem.description = "A completely rewritten description."
    db_session.commit()

    assert [p.title for p in find_stale(db_session, embedder)] == ["Problem number 1"]
    assert reindex(db_session, embedder)["embedded"] == 1


def test_changing_a_field_that_is_not_embedded_leaves_the_vector_current(db_session):
    seed(db_session)
    embedder = HashingEmbedder()
    reindex(db_session, embedder)
    problem = db_session.scalars(select(Problem)).first()

    problem.impact_level = "critical"
    db_session.commit()

    assert find_stale(db_session, embedder) == []


def test_switching_models_makes_every_vector_stale(db_session):
    seed(db_session)
    reindex(db_session, HashingEmbedder())

    assert len(find_stale(db_session, OtherModel())) == 3
    assert reindex(db_session, OtherModel())["embedded"] == 3
    assert {m for (m,) in db_session.execute(select(ProblemEmbedding.model_name))} == {"other-model-test"}


def test_creating_updating_and_ingesting_problems_never_embeds(client, db_session):
    created = client.post("/problems", json={"title": "Created through the API"}).json()
    client.patch(f"/problems/{created['id']}", json={"description": "Edited later."})
    seed(db_session)

    assert embedded_count(db_session) == 0
    assert len(find_stale(db_session, HashingEmbedder())) == 4  # flagged for the indexing command


def test_embedder_with_the_wrong_dimension_is_rejected_before_writing(db_session):
    seed(db_session)

    with pytest.raises(ValueError, match="384"):
        reindex(db_session, FixedEmbedder({}, dimensions=8))
    assert embedded_count(db_session) == 0


def test_deleting_a_problem_removes_its_embedding(client, db_session):
    seed(db_session, count=1)
    reindex(db_session, HashingEmbedder())
    problem_id = db_session.scalars(select(Problem.id)).one()

    assert client.delete(f"/problems/{problem_id}").status_code == 204
    db_session.expire_all()

    assert embedded_count(db_session) == 0


def test_source_text_uses_title_description_and_category():
    problem = Problem(title=" Gate queues ", description="Drivers wait.", category="Access")
    assert embedding_source_text(problem) == "Gate queues. Drivers wait.. Access"
    assert embedding_source_text(Problem(title="Only a title")) == "Only a title"


def test_status_reports_progress(db_session):
    seed(db_session)
    embedder = HashingEmbedder()

    before = status(db_session, embedder)
    reindex(db_session, embedder)
    after = status(db_session, embedder)

    assert (before["indexed"], before["stale"], before["available"]) == (0, 3, False)
    assert (after["indexed"], after["stale"], after["available"]) == (3, 0, True)
    assert after["model_name"] == "hashing-test" and after["total_problems"] == 3
    assert status(db_session, None)["provider_enabled"] is False
