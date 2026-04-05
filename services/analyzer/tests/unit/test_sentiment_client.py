from unittest.mock import Mock

import pytest
from src.clients.ml_sentiment_client import SentimentClient


def _ready_client() -> SentimentClient:
    client = SentimentClient(mlflow_uri="http://mlflow.test")
    client.model_version = "test_v1"
    client._is_loaded = True
    client.model = Mock()
    return client


def test_predict_sentiment_raises_when_model_not_loaded():
    client = SentimentClient(mlflow_uri="http://mlflow.test")

    with pytest.raises(RuntimeError, match="model not loaded"):
        client.predict_sentiment("hello")


def test_predict_sentiment_returns_reliable_payload():
    client = _ready_client()
    client.model.predict.return_value = [
        {
            "sentiment": "positive",
            "confidence": 0.9,
            "confidence_level": "high",
            "all_scores": {"positive": 0.9},
        }
    ]

    result = client.predict_sentiment("great day")

    assert result["sentiment"] == "positive"
    assert result["is_reliable"] is True
    assert result["ml_model_version"] == "test_v1"
    assert result["reason"] == "High confidence classification"


def test_predict_sentiment_returns_unreliable_payload():
    client = _ready_client()
    client.model.predict.return_value = [
        {
            "sentiment": "negative",
            "confidence": 0.2,
            "confidence_level": "low",
        }
    ]

    result = client.predict_sentiment("bad day")

    assert result["sentiment"] == "negative"
    assert result["is_reliable"] is False
    assert result["all_scores"] == {}
    assert result["reason"] == "Low confidence - consider as uncertain"


def test_predict_sentiment_batch_processes_multiple_results():
    client = _ready_client()
    client.model.predict.return_value = [
        {"sentiment": "positive", "confidence": 0.8, "confidence_level": "high"},
        {"sentiment": "neutral", "confidence": 0.3, "confidence_level": "low"},
    ]

    results = client.predict_sentiment_batch(["one", "two"])

    assert len(results) == 2
    assert results[0]["is_reliable"] is True
    assert results[1]["is_reliable"] is False
    assert results[1]["reason"] == "Low confidence - consider as uncertain"


def test_get_sentiment_simple_returns_label():
    client = _ready_client()
    client.model.predict.return_value = [{"sentiment": "neutral", "confidence": 0.8}]

    assert client.get_sentiment_simple("fine") == "neutral"


def test_classify_with_confidence_check_returns_uncertain_when_unreliable():
    client = _ready_client()
    client.model.predict.return_value = [
        {"sentiment": "positive", "confidence": 0.2, "confidence_level": "low"}
    ]

    result = client.classify_with_confidence_check("mixed")

    assert result["sentiment"] == "uncertain"
    assert result["original_prediction"] == "positive"
    assert "below threshold" in result["details"]


def test_classify_with_confidence_check_returns_prediction_when_reliable():
    client = _ready_client()
    client.model.predict.return_value = [
        {"sentiment": "positive", "confidence": 0.7, "confidence_level": "medium"}
    ]

    result = client.classify_with_confidence_check("mixed")

    assert result["sentiment"] == "positive"
    assert result["reason"] == "High confidence classification"


def test_analyze_sentiment_trends_summarizes_predictions():
    client = _ready_client()
    client.model.predict.return_value = [
        {"sentiment": "positive", "confidence": 0.9, "confidence_level": "high"},
        {"sentiment": "negative", "confidence": 0.2, "confidence_level": "low"},
    ]

    result = client.analyze_sentiment_trends(
        [
            {"text": "good", "date": "2026-04-01"},
            {"text": "bad", "date": "2026-04-02"},
        ]
    )

    assert result["total_entries"] == 2
    assert result["overall_distribution"]["positive"] == 1
    assert result["overall_distribution"]["uncertain"] == 1
    assert result["dominant_sentiment"] == "positive"
    assert result["analysis_summary"]["reliability"] == "50.0%"
