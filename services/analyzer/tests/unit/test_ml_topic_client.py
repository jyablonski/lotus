from unittest.mock import Mock

from src.clients.ml_topic_client import TopicClient


def _client() -> TopicClient:
    client = TopicClient()
    client.model_version = "topic_v1"
    client.model = Mock()
    return client


def test_extract_topics_adds_model_version():
    client = _client()
    client.model.predict.return_value = [{"topics": [{"topic_name": "Work", "confidence": 0.9}]}]

    result = client.extract_topics("hello")

    assert result == [{"topic_name": "Work", "confidence": 0.9, "ml_model_version": "topic_v1"}]


def test_extract_topics_batch_adds_model_version():
    client = _client()
    client.model.predict.return_value = [
        {"topics": [{"topic_name": "Work", "confidence": 0.9}]},
        {"topics": [{"topic_name": "Sleep", "confidence": 0.7}]},
    ]

    result = client.extract_topics_batch(["one", "two"])

    assert result == [
        [{"topic_name": "Work", "confidence": 0.9, "ml_model_version": "topic_v1"}],
        [{"topic_name": "Sleep", "confidence": 0.7, "ml_model_version": "topic_v1"}],
    ]


def test_get_top_topic_returns_first_topic():
    client = _client()
    client.model.predict.return_value = [
        {
            "topics": [
                {"topic_name": "Work", "confidence": 0.9},
                {"topic_name": "Stress", "confidence": 0.8},
            ]
        }
    ]

    assert client.get_top_topic("hello") == {
        "topic_name": "Work",
        "confidence": 0.9,
        "ml_model_version": "topic_v1",
    }


def test_get_top_topic_returns_none_when_no_topics():
    client = _client()
    client.model.predict.return_value = [{"topics": []}]

    assert client.get_top_topic("hello") is None
