from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from src.clients.openai_topic_client import OpenAITopicClient
from src.schemas.openai_topics import AnalysisRequest


@pytest.fixture
def anyio_backend():
    return "asyncio"


@contextmanager
def _noop_run():
    yield


def _client_with_mocked_backend():
    client = OpenAITopicClient.__new__(OpenAITopicClient)
    client.client = Mock()
    client.client.chat = Mock()
    client.client.chat.completions = Mock()
    client.model = "gpt-test"
    return client


@pytest.mark.anyio
async def test_analyze_topics_logs_params_metrics_and_returns_topics(monkeypatch):
    client = _client_with_mocked_backend()
    result = Mock()
    result.topics = ["work", "stress"]
    result.confidence_scores = [0.9, 0.7]

    create = AsyncMock(return_value=result)
    client.client.chat.completions.create = create

    set_tracking_uri = Mock()
    set_experiment = Mock()
    start_run = Mock(return_value=_noop_run())
    log_params = Mock()
    log_metrics = Mock()

    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.set_tracking_uri", set_tracking_uri)
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.set_experiment", set_experiment)
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.start_run", start_run)
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.log_params", log_params)
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.log_metrics", log_metrics)

    response = await client.analyze_topics(AnalysisRequest(text="hello world", max_topics=2))

    assert response.topics == ["work", "stress"]
    assert response.confidence_scores == [0.9, 0.7]
    set_tracking_uri.assert_called_once()
    set_experiment.assert_called_once()
    start_run.assert_called_once_with(run_name="openai_topic_analysis")
    log_params.assert_called_once()
    log_metrics.assert_called_once_with(
        {
            "avg_confidence": 0.8,
            "min_confidence": 0.7,
            "max_confidence": 0.9,
        }
    )

    kwargs = create.await_args.kwargs
    assert kwargs["model"] == "gpt-test"
    assert kwargs["temperature"] > 0
    assert "exactly 2 distinct topics" in kwargs["messages"][0]["content"]


@pytest.mark.anyio
async def test_analyze_topics_skips_metrics_for_empty_confidence_scores(monkeypatch):
    client = _client_with_mocked_backend()
    result = Mock()
    result.topics = []
    result.confidence_scores = []
    client.client.chat.completions.create = AsyncMock(return_value=result)

    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.set_tracking_uri", Mock())
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.set_experiment", Mock())
    monkeypatch.setattr(
        "src.clients.openai_topic_client.mlflow.start_run", Mock(return_value=_noop_run())
    )
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.log_params", Mock())
    log_metrics = Mock()
    monkeypatch.setattr("src.clients.openai_topic_client.mlflow.log_metrics", log_metrics)

    response = await client.analyze_topics(AnalysisRequest(text="hello", max_topics=0))

    assert response.topics == []
    assert response.confidence_scores == []
    log_metrics.assert_not_called()
