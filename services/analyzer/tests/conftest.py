from datetime import datetime
import logging
from pathlib import Path
import pickle
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
import pytest
from src.clients.ml_sentiment_client import SentimentClient
from src.clients.ml_topic_client import TopicClient
from src.dependencies import get_db
from src.main import app
from src.models.journal_sentiments import JournalSentiments
from src.models.journals import Journals
from src.schemas.openai_topics import TopicAnalysis

logger = logging.getLogger(__name__)

TEST_FIXTURES_DIR = Path("tests/fixtures/models")
SENTIMENT_MODEL_PATH = TEST_FIXTURES_DIR / "sentiment_test_model.pkl"
TOPIC_MODEL_PATH = TEST_FIXTURES_DIR / "topic_test_model.pkl"


@pytest.fixture(scope="session")
def real_sentiment_client():
    """Load pre-saved sentiment model for testing."""
    logger.info("Loading test sentiment model from fixtures...")

    if not SENTIMENT_MODEL_PATH.exists():
        pytest.skip(f"Test sentiment model not found at {SENTIMENT_MODEL_PATH}")

    try:
        with SENTIMENT_MODEL_PATH.open("rb") as f:
            test_pipeline = pickle.load(f)

        client = SentimentClient()

        client.sentiment_pipeline = test_pipeline
        client.model = test_pipeline
        client.model_version = "test_v1.0.0"
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
    """Load pre-saved topic model for testing."""
    logger.info("Loading test topic model from fixtures...")

    if not TOPIC_MODEL_PATH.exists():
        pytest.skip(f"Test topic model not found at {TOPIC_MODEL_PATH}.")

    try:
        # Load the pre-saved pipeline
        with Path.open(TOPIC_MODEL_PATH, "rb") as f:
            test_pipeline = pickle.load(f)

        # Create client and inject the test model
        client = TopicClient()
        client.topic_pipeline = test_pipeline
        client.model = test_pipeline
        client.model_version = "test_v1.0.0"
        client._is_loaded = True

        # Set up topic labels (you may need to adjust these based on your model)
        client.topic_labels = {
            0: "Daily Needs & Work",
            1: "Evening Reflection",
            2: "Work & Productivity",
            3: "Emotional State",
            4: "Feelings & Emotions",
            5: "Daily Activities",
            6: "Morning Routine & Positivity",
            7: "Work Focus & Effort",
        }

        # Verify it works
        test_result = client.extract_topics("This is a test")
        assert isinstance(test_result, list)

        logger.info("Test topic model loaded successfully")
        return client

    except Exception as e:
        logger.error(f"Failed to load test topic model: {e}")
        pytest.skip(f"Test topic model could not be loaded: {e}")


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
def client_fixture():
    client = TestClient(app)

    return client


@pytest.fixture
def mock_topic_client():
    """Mock TopicClient for tests."""
    client = Mock(spec=TopicClient)
    client.is_ready.return_value = True
    client.model_version = "test_v1"

    client.extract_topics.return_value = [
        {
            "topic_name": "Work & Productivity",
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
    return mock_client
