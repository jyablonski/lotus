from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.ml.topic_client import TopicClient


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
