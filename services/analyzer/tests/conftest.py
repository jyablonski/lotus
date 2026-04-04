import os

# Must be set before any src imports — main.py raises RuntimeError at module
# level if ANALYZER_API_KEY is missing, and database.py reads ENV_TYPE at import.
os.environ.setdefault("ANALYZER_API_KEY", "test-key")
os.environ.setdefault("ENV_TYPE", "dev")
# Prevent the OTel OTLP exporter from retrying indefinitely when there is no
# collector running in CI. The background BatchSpanProcessor thread will fail
# immediately instead of hanging until after pytest closes its log streams,
# which would produce "ValueError: I/O operation on closed file" and cause a
# non-zero exit code via pytest's threading.excepthook capture.
os.environ.setdefault("OTEL_BSP_SCHEDULE_DELAY_MILLIS", "1")
os.environ.setdefault("OTEL_BSP_EXPORT_TIMEOUT_MILLIS", "100")

from datetime import datetime
import logging
from pathlib import Path
import pickle
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
import pandas as pd
import psycopg2
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.clients.ml_sentiment_client import SentimentClient
from src.clients.ml_topic_client import TopicClient
from src.dependencies import get_db
from src.main import app
from src.models.journal_sentiments import JournalSentiments
from src.models.journals import Journals
from src.schemas.openai_topics import TopicAnalysis
from testcontainers.postgres import PostgresContainer

logger = logging.getLogger(__name__)

TEST_FIXTURES_DIR = Path("tests/fixtures/models")
SENTIMENT_MODEL_PATH = TEST_FIXTURES_DIR / "sentiment_test_model.pkl"

# Path to the bootstrap SQL relative to the repo root, resolved from this file's location.
# conftest.py lives at services/analyzer/tests/conftest.py → 3 parents up = repo root.
_BOOTSTRAP_SQL = Path(__file__).parents[3] / "docker/db/01-bootstrap.sql"
_SOURCE_SCHEMA_SQL = Path(__file__).parents[3] / "docker/db/generated/ci_source_schema.sql"
_SEED_DATA_SQL = Path(__file__).parent / "fixtures/sql/seed_source_data.sql"

_TEST_API_KEY = os.environ["ANALYZER_API_KEY"]


@pytest.fixture(scope="session", autouse=True)
def shutdown_otel_providers():
    """Cleanly shut down OTel providers after the test session.

    The BatchSpanProcessor starts a background thread on import of src.main.
    Without an explicit shutdown() that thread keeps running after pytest
    finishes, then tries to log into already-closed streams → ValueError.
    Shutting down the provider here drains and stops the background thread
    before pytest tears down its logging infrastructure.
    """
    yield
    import contextlib

    from opentelemetry import (
        metrics as otel_metrics,
        trace,
    )

    with contextlib.suppress(Exception):
        trace.get_tracer_provider().shutdown()
    with contextlib.suppress(Exception):
        otel_metrics.get_meter_provider().shutdown()


class MockPyfuncSentimentModel:
    """
    Mock pyfunc model that wraps a sklearn pipeline
    and provides the same interface as the production pyfunc wrapper.
    """

    def __init__(self, sklearn_pipeline):
        self.pipeline = sklearn_pipeline
        self.sentiment_labels = {0: "negative", 1: "neutral", 2: "positive"}
        self.confidence_thresholds = {"high": 0.7, "medium": 0.5, "low": 0.3}

    def predict(self, model_input: pd.DataFrame) -> list[dict]:
        """Mimic the pyfunc wrapper's predict method."""
        if "text" not in model_input.columns:
            raise ValueError("model_input must contain 'text' column")

        texts = model_input["text"].tolist()
        results = []

        for text in texts:
            # Preprocess
            processed_text = text.lower().strip()

            # Get prediction and probabilities from sklearn pipeline
            prediction = self.pipeline.predict([processed_text])[0]
            probabilities = self.pipeline.predict_proba([processed_text])[0]

            sentiment = self.sentiment_labels[prediction]
            confidence = float(max(probabilities))

            # Determine confidence level
            if confidence >= self.confidence_thresholds["high"]:
                confidence_level = "high"
            elif confidence >= self.confidence_thresholds["medium"]:
                confidence_level = "medium"
            else:
                confidence_level = "low"

            results.append(
                {
                    "sentiment": sentiment,
                    "confidence": round(confidence, 4),
                    "confidence_level": confidence_level,
                    "all_scores": {
                        self.sentiment_labels[i]: round(float(prob), 4)
                        for i, prob in enumerate(probabilities)
                    },
                }
            )

        return results


class MockSemanticTopicModel:
    """Mock pyfunc model matching the SemanticTopicExtractorWrapper output format.

    Returns keyword-heuristic topics so integration tests can exercise the full
    HTTP → DB → response path without loading the real sentence-transformer model.
    """

    def predict(self, model_input: pd.DataFrame) -> list[dict]:
        if "text" not in model_input.columns:
            raise ValueError("model_input must contain 'text' column")

        texts = model_input["text"].tolist()
        results = []

        for text in texts:
            lower = text.lower()
            word_count = len(text.split())
            top_n = 2 if word_count < 20 else (4 if word_count < 50 else 6)

            candidates = []
            if any(w in lower for w in ["work", "meeting", "boss", "deadline", "office"]):
                candidates.append({"topic_name": "work and career", "confidence": 0.82})
            if any(w in lower for w in ["stress", "anxious", "overwhelm", "drained"]):
                candidates.append({"topic_name": "stress and overwhelm", "confidence": 0.75})
            if any(w in lower for w in ["happy", "joy", "amazing", "wonderful", "great"]):
                candidates.append({"topic_name": "joy and happiness", "confidence": 0.78})
            if any(w in lower for w in ["sleep", "tired", "rest", "exhausted"]):
                candidates.append({"topic_name": "sleep and rest", "confidence": 0.71})
            if any(w in lower for w in ["grateful", "thankful", "gratitude", "appreciate"]):
                candidates.append({"topic_name": "gratitude and appreciation", "confidence": 0.80})
            if any(w in lower for w in ["run", "gym", "exercise", "workout", "fitness"]):
                candidates.append({"topic_name": "physical health and fitness", "confidence": 0.77})

            if not candidates:
                candidates = [{"topic_name": "reflection and introspection", "confidence": 0.60}]

            results.append({"topics": candidates[:top_n]})

        return results


# ---------------------------------------------------------------------------
# Testcontainers: Postgres
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container():
    """Spin up an isolated Postgres container for the entire test session."""
    with PostgresContainer("pgvector/pgvector:pg16") as pg:
        conn = psycopg2.connect(
            host=pg.get_container_host_ip(),
            port=pg.get_exposed_port(5432),
            user=pg.username,
            password=pg.password,
            dbname=pg.dbname,
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            # Apply bootstrap (schemas/extensions) first, then the generated
            # source schema artifact (tables/constraints). CREATE DATABASE is
            # skipped because testcontainers already provides its own DB.
            bootstrap_sql = "\n".join(
                line
                for line in _BOOTSTRAP_SQL.read_text().splitlines()
                if not line.strip().upper().startswith("CREATE DATABASE")
            )
            cur.execute(bootstrap_sql)
            cur.execute(_SOURCE_SCHEMA_SQL.read_text())
            cur.execute(_SEED_DATA_SQL.read_text())
        conn.close()
        yield pg


@pytest.fixture(scope="session")
def test_engine(postgres_container):
    """SQLAlchemy engine pointed at the testcontainer with source schema."""
    engine = create_engine(
        postgres_container.get_connection_url(),
        connect_args={"options": "-csearch_path=source"},
    )
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_engine):
    """Fresh SQLAlchemy session per test; rolls back after each test."""
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, future=True)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ---------------------------------------------------------------------------
# Existing fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_sentiment_client():
    """Load pre-saved sentiment model for testing."""
    logger.info("Loading test sentiment model from fixtures...")

    if not SENTIMENT_MODEL_PATH.exists():
        pytest.skip(f"Test sentiment model not found at {SENTIMENT_MODEL_PATH}")

    try:
        with SENTIMENT_MODEL_PATH.open("rb") as f:
            test_pipeline = pickle.load(f)

        # Create client and inject mock pyfunc model
        client = SentimentClient()
        client.model = MockPyfuncSentimentModel(test_pipeline)
        client.model_version = "test_v1.0.0"
        client.model_run_id = "test_run_id"
        client._is_loaded = True

        # Verify it works
        test_result = client.predict_sentiment("This is a test")
        assert "sentiment" in test_result

        logger.info("Test sentiment model loaded successfully")
        return client

    except Exception as e:
        logger.error(f"Failed to load test sentiment model: {e}")
        pytest.skip(f"Test sentiment model could not be loaded: {e}")


@pytest.fixture(scope="session")
def real_topic_client():
    """Topic client with a lightweight mock semantic model for integration tests.

    Uses MockSemanticTopicModel instead of loading the real sentence-transformer
    so tests run without network access or large model downloads.
    """
    client = TopicClient()
    client.model = MockSemanticTopicModel()
    client.model_version = "test_v1.0.0"
    client.model_run_id = "test_run_id"
    client._is_loaded = True

    # Verify it works
    test_result = client.extract_topics("This is a test entry about work")
    assert isinstance(test_result, list)

    logger.info("Test topic client (semantic mock) ready")
    return client


@pytest.fixture
def override_db_dependency(test_db_session):
    """Override database dependency to use test database."""

    def get_test_db():
        return test_db_session

    app.dependency_overrides[get_db] = get_test_db

    yield test_db_session

    # Clean up dependency override
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture
def client_fixture(override_db_dependency):
    """TestClient with auth header and testcontainer DB wired up via override_db_dependency."""
    client = TestClient(app, headers={"Authorization": f"Bearer {_TEST_API_KEY}"})

    return client


@pytest.fixture
def mock_topic_client():
    """Mock TopicClient for tests."""
    client = Mock(spec=TopicClient)
    client.is_ready.return_value = True
    client.model_version = "test_v1"

    client.extract_topics.return_value = [
        {
            "topic_name": "work and career",
            "confidence": 0.85,
            "ml_model_version": "test_v1",
        }
    ]

    client.get_model_info.return_value = {
        "status": "loaded",
        "model_version": "test_v1",
    }

    return client


@pytest.fixture
def mock_sentiment_client():
    """Mock sentiment client for testing."""
    mock_client = Mock()
    mock_client.predict_sentiment.return_value = {
        "sentiment": "positive",
        "confidence": 0.8234,
        "confidence_level": "high",
        "is_reliable": True,
        "all_scores": {"positive": 0.8234, "negative": 0.1234, "neutral": 0.0532},
        "ml_model_version": "v1.0.0",
    }
    mock_client.model_version = "v1.0.0"
    mock_client.is_ready.return_value = True
    return mock_client


@pytest.fixture
def mock_journal():
    """Mock journal object for testing."""
    journal = Mock(spec=Journals)
    journal.id = 1
    journal.journal_text = "Today was a wonderful day! I accomplished so much."
    return journal


@pytest.fixture
def mock_sentiment_record():
    """Mock sentiment analysis record."""
    record = Mock(spec=JournalSentiments)
    record.id = 1
    record.journal_id = 1
    record.sentiment = "positive"
    record.confidence = 0.8234
    record.confidence_level = "high"
    record.is_reliable = True
    record.ml_model_version = "v1.0.0"
    record.created_at = datetime(2024, 1, 15, 14, 30, 0)
    record.all_scores = {"positive": 0.8234, "negative": 0.1234, "neutral": 0.0532}
    return record


@pytest.fixture
def mock_openai_topic_client():
    """Mock OpenAI topic client with realistic responses."""

    async def mock_analyze_topics(request):
        # Return realistic mock data based on request
        if "work" in request.text.lower() or "meeting" in request.text.lower():
            return TopicAnalysis(
                topics=["work", "stress", "meetings", "productivity", "deadlines"][
                    : request.max_topics
                ],
                confidence_scores=[0.95, 0.88, 0.82, 0.75, 0.70][: request.max_topics],
            )
        if "date" in request.text.lower() or "girlfriend" in request.text.lower():
            return TopicAnalysis(
                topics=["love", "relationship", "happiness", "date", "romance"][
                    : request.max_topics
                ],
                confidence_scores=[0.92, 0.89, 0.85, 0.80, 0.75][: request.max_topics],
            )
        # Generic response
        return TopicAnalysis(
            topics=["general", "life", "thoughts", "feelings", "day"][: request.max_topics],
            confidence_scores=[0.70, 0.65, 0.60, 0.55, 0.50][: request.max_topics],
        )

    mock_client = AsyncMock()
    mock_client.analyze_topics = mock_analyze_topics
    mock_client.model = "gpt-4o-mini"
    return mock_client
