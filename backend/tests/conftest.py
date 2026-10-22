import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.company import Company  # noqa: F401
from app.models.problem import Problem  # noqa: F401
from app.models.company_problem import CompanyProblem  # noqa: F401
from app.models.source import Source  # noqa: F401
from app.models.evidence import EvidenceRecord  # noqa: F401
from app.models.ingestion_run import IngestionRun  # noqa: F401

from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/problem_intelligence_test"

test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure all database schema tables exist in problem_intelligence_test."""
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.commit()
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    # Tables are retained for fast test runs, individual test cleanup truncates rows.


@pytest.fixture(autouse=True)
def clean_database():
    """Truncate tables before each test to ensure test isolation."""
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE companies, problems, sources, evidence_records, ingestion_runs RESTART IDENTITY CASCADE;"))
        conn.commit()


    yield


@pytest.fixture
def db_session():
    """Yield an isolated database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide FastAPI TestClient with get_db overridden to use test database session."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
