from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.ml.topic_client import TopicClient
from src.models.journal_sentiments import JournalSentiments
from src.models.journals import Journals


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
