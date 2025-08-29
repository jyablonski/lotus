from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.ml.topic_client import TopicClient


@pytest.fixture
def mock_mlflow():
    """Mock MLflow for TopicClient tests."""
    with patch("src.ml.topic_client.mlflow") as mock_mlflow:
        # Mock the sklearn model - return numpy array, not list
        mock_model = Mock()
        mock_model.transform.return_value = np.array(
            [[0.1, 0.2, 0.85, 0.05, 0.3, 0.72, 0.4, 0.15]]
        )
        mock_mlflow.sklearn.load_model.return_value = mock_model

        # Mock the MLflow client
        mock_client = Mock()
        mock_version = Mock()
        mock_version.version = "3"
        mock_client.search_model_versions.return_value = [
            Mock(version="1"),
            Mock(version="2"),
            mock_version,
        ]
        mock_client.get_model_version.return_value = Mock(run_id="test_run_456")
        mock_mlflow.MlflowClient.return_value = mock_client

        yield mock_mlflow


def test_topic_client_load_model(mock_mlflow):
    """Test model loading."""
    client = TopicClient()
    client.load_model("latest")

    assert client.is_ready()
    assert client.model_version == "3"
    assert client.model_run_id == "test_run_456"


def test_topic_client_extract_topics_high_confidence(mock_mlflow):
    """Test topic extraction with high confidence."""
    client = TopicClient()
    client.load_model("latest")

    topics = client.extract_topics("I had a great day at work today")

    assert len(topics) == 7  # Based on mock probabilities > 0.1
    assert topics[0]["topic_name"] == "Work & Productivity"  # Highest confidence (0.85)
    assert topics[0]["confidence"] == 0.85
    assert topics[0]["ml_model_version"] == "3"
    assert topics[1]["topic_name"] == "Daily Activities"  # Second highest (0.72)


def test_topic_client_extract_topics_low_confidence(mock_mlflow):
    """Test topic extraction returns 'Other' for low confidence."""
    # Mock low confidence probabilities (all below 0.4 threshold)
    mock_model = Mock()
    mock_model.transform.return_value = np.array(
        [[0.1, 0.05, 0.25, 0.08, 0.12, 0.09, 0.11, 0.06]]
    )

    with patch.object(mock_mlflow.sklearn, "load_model", return_value=mock_model):
        client = TopicClient()
        client.load_model("latest")

        topics = client.extract_topics("unclear text")

        assert len(topics) == 1
        assert topics[0]["topic_name"] == "Other"
        assert "reason" in topics[0]


def test_topic_client_not_ready():
    """Test methods fail when client not ready."""
    client = TopicClient()

    assert not client.is_ready()

    with pytest.raises(RuntimeError, match="TopicClient model not loaded"):
        client.extract_topics("test text")


def test_get_top_topic(mock_mlflow):
    """Test getting the top topic."""
    client = TopicClient()
    client.load_model("latest")

    top_topic = client.get_top_topic("I worked hard today")

    assert top_topic["topic_name"] == "Work & Productivity"
    assert top_topic["confidence"] == 0.85
    assert top_topic["ml_model_version"] == "3"


def test_classify_with_confidence_check_high_confidence(mock_mlflow):
    """Test classification with high confidence."""
    client = TopicClient()
    client.load_model("latest")

    result = client.classify_with_confidence_check("I had a productive work day")

    assert result["topic_name"] == "Work & Productivity"
    assert result["confidence"] == 0.85
    assert result["reason"] == "High confidence classification"


def test_get_model_info(mock_mlflow):
    """Test getting model information."""
    client = TopicClient()
    client.load_model("latest")

    info = client.get_model_info()

    assert info["status"] == "loaded"
    assert info["model_name"] == "adaptive_journal_topics"
    assert info["model_version"] == "3"
    assert info["run_id"] == "test_run_456"


def test_get_model_info_not_loaded():
    """Test getting model info when not loaded."""
    client = TopicClient()

    info = client.get_model_info()

    assert info["status"] == "not_loaded"
