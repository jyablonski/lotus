import logging
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.ml.sentiment_client import SentimentClient
from src.ml.topic_client import TopicClient
from src.models.journal_sentiments import JournalSentiments
from src.models.journals import Journals

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def real_sentiment_client():
    """Load real sentiment analysis model once per test session."""
    logger.info("Loading real sentiment analysis model for tests...")

    try:
        client = SentimentClient()
        client.load_model()

        # Verify model is working
        test_result = client.predict_sentiment("This is a test")
        assert "sentiment" in test_result

        logger.info(f"Sentiment model loaded successfully: {client.get_model_info()}")
        return client

    except Exception as e:
        logger.error(f"Failed to load sentiment model for tests: {e}")
        pytest.skip(f"Sentiment model not available for testing: {e}")


@pytest.fixture(scope="session")
def real_topic_client():
    """Load real topic extraction model once per test session."""
    logger.info("Loading real topic extraction model for tests...")

    try:
        client = TopicClient()
        client.load_model()

        # Verify model is working
        test_result = client.extract_topics("This is a test")
        assert isinstance(test_result, list)

        logger.info(f"Topic model loaded successfully: {client.get_model_info()}")
        return client

    except Exception as e:
        logger.error(f"Failed to load topic model for tests: {e}")
        pytest.skip(f"Topic model not available for testing: {e}")


@pytest.fixture
def override_db_dependency(test_db_session):
    """Override database dependency to use test database."""
    from src.dependencies import get_db
    from src.main import app

    def get_test_db():
        return test_db_session

    app.dependency_overrides[get_db] = get_test_db

    yield test_db_session

    # Clean up dependency override
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture()
def client_fixture():
    client = TestClient(app)

    yield client


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
