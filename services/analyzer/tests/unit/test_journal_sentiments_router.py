from unittest.mock import Mock

from fastapi import HTTPException
import pytest
from src.routers.v1 import journal_sentiments as router_module
from src.schemas.sentiments import BulkSentimentAnalysisRequest, SentimentAnalysisRequest


def test_analyze_journal_sentiment_returns_404_when_journal_missing():
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        router_module.analyze_journal_sentiment(
            journal_id=99,
            request=SentimentAnalysisRequest(force_reanalyze=False),
            sentiment_client=Mock(),
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Journal entry not found"


def test_analyze_journal_sentiment_returns_500_when_prediction_fails():
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = Mock(journal_text="hello")
    sentiment_client = Mock()
    sentiment_client.predict_sentiment.side_effect = RuntimeError("boom")

    with pytest.raises(HTTPException) as exc_info:
        router_module.analyze_journal_sentiment(
            journal_id=1,
            request=SentimentAnalysisRequest(force_reanalyze=False),
            sentiment_client=sentiment_client,
            db=db,
        )

    assert exc_info.value.status_code == 500
    assert "Sentiment analysis failed" in exc_info.value.detail


def test_analyze_journal_sentiment_returns_500_when_db_write_fails(monkeypatch):
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = Mock(journal_text="hello")
    sentiment_client = Mock()
    sentiment_client.predict_sentiment.return_value = {"sentiment": "positive", "score": 0.9}
    monkeypatch.setattr(
        router_module,
        "create_or_update_sentiment",
        Mock(side_effect=RuntimeError("db boom")),
    )

    with pytest.raises(HTTPException) as exc_info:
        router_module.analyze_journal_sentiment(
            journal_id=1,
            request=SentimentAnalysisRequest(force_reanalyze=False),
            sentiment_client=sentiment_client,
            db=db,
        )

    assert exc_info.value.status_code == 500
    assert "Database operation failed" in exc_info.value.detail


def test_get_journal_sentiment_returns_404_when_missing(monkeypatch):
    monkeypatch.setattr(router_module, "get_sentiment_by_journal_id", Mock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        router_module.get_journal_sentiment(journal_id=1, model_version=None, db=Mock())

    assert exc_info.value.status_code == 404


def test_update_journal_sentiment_forces_reanalyze(monkeypatch):
    captured = {}

    def fake_analyze(journal_id, request, sentiment_client, db):
        captured["force_reanalyze"] = request.force_reanalyze
        return {"ok": True}

    monkeypatch.setattr(router_module, "analyze_journal_sentiment", fake_analyze)

    response = router_module.update_journal_sentiment(
        journal_id=1,
        request=SentimentAnalysisRequest(force_reanalyze=False),
        sentiment_client=Mock(),
        db=Mock(),
    )

    assert response == {"ok": True}
    assert captured["force_reanalyze"] is True


def test_delete_journal_sentiment_returns_404_when_nothing_deleted(monkeypatch):
    monkeypatch.setattr(router_module, "delete_sentiment", Mock(return_value=0))

    with pytest.raises(HTTPException) as exc_info:
        router_module.delete_journal_sentiment(journal_id=1, model_version=None, db=Mock())

    assert exc_info.value.status_code == 404


def test_delete_journal_sentiment_returns_response(monkeypatch):
    monkeypatch.setattr(router_module, "delete_sentiment", Mock(return_value=2))

    response = router_module.delete_journal_sentiment(journal_id=1, model_version=None, db=Mock())

    assert response.deleted_count == 2
    assert response.journal_id == 1


def test_analyze_journals_sentiment_batch_returns_404_for_missing_ids():
    request = BulkSentimentAnalysisRequest(journal_ids=[1, 2], force_reanalyze=False)
    db = Mock()
    db.query.return_value.filter.return_value.all.return_value = [Mock(id=1)]

    with pytest.raises(HTTPException) as exc_info:
        router_module.analyze_journals_sentiment_batch(
            request=request,
            sentiment_client=Mock(),
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert "Journal entries not found" in exc_info.value.detail


def test_analyze_journals_sentiment_batch_continues_on_per_item_failure(monkeypatch):
    journals = [
        Mock(id=1, journal_text="good"),
        Mock(id=2, journal_text="bad"),
    ]
    db = Mock()
    db.query.return_value.filter.return_value.all.return_value = journals
    sentiment_client = Mock()
    sentiment_client.predict_sentiment.side_effect = [
        {"sentiment": "positive", "score": 0.9},
        RuntimeError("boom"),
    ]
    monkeypatch.setattr(
        router_module,
        "create_or_update_sentiment",
        Mock(return_value=Mock(journal_id=1)),
    )

    results = router_module.analyze_journals_sentiment_batch(
        request=BulkSentimentAnalysisRequest(journal_ids=[1, 2], force_reanalyze=False),
        sentiment_client=sentiment_client,
        db=db,
    )

    assert len(results) == 1
    assert results[0].journal_id == 1


def test_get_sentiment_trends_endpoint_rejects_invalid_group_by():
    with pytest.raises(HTTPException) as exc_info:
        router_module.get_sentiment_trends_endpoint(
            user_id=None,
            days_back=30,
            group_by="year",
            reliable_only=True,
            db=Mock(),
        )

    assert exc_info.value.status_code == 400


def test_get_sentiment_trends_endpoint_transforms_results(monkeypatch):
    monkeypatch.setattr(
        router_module,
        "get_sentiment_trends",
        Mock(
            return_value=[
                {
                    "period": "2026-04-01",
                    "sentiment_counts": {"positive": 2},
                    "avg_confidence": 0.75,
                    "total_entries": 2,
                    "dominant_sentiment": "positive",
                }
            ]
        ),
    )

    results = router_module.get_sentiment_trends_endpoint(
        user_id=None,
        days_back=30,
        group_by="day",
        reliable_only=True,
        db=Mock(),
    )

    assert len(results) == 1
    assert results[0].period == "2026-04-01"
    assert results[0].dominant_sentiment == "positive"


def test_get_sentiment_stats_endpoint_returns_404_when_empty(monkeypatch):
    monkeypatch.setattr(
        router_module,
        "get_sentiment_stats",
        Mock(
            return_value={
                "total_analyzed": 0,
                "reliable_count": 0,
                "reliability_rate": 0.0,
                "sentiment_distribution": {"positive": 0},
                "avg_confidence": 0.0,
                "latest_model_version": None,
            }
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        router_module.get_sentiment_stats_endpoint(user_id=None, days_back=None, db=Mock())

    assert exc_info.value.status_code == 404


def test_get_sentiment_stats_endpoint_returns_stats(monkeypatch):
    monkeypatch.setattr(
        router_module,
        "get_sentiment_stats",
        Mock(
            return_value={
                "total_analyzed": 3,
                "reliable_count": 2,
                "reliability_rate": 2 / 3,
                "sentiment_distribution": {
                    "positive": 1,
                    "negative": 1,
                    "neutral": 1,
                    "uncertain": 0,
                },
                "avg_confidence": 0.7,
                "latest_model_version": "test_v1",
            }
        ),
    )

    response = router_module.get_sentiment_stats_endpoint(user_id=None, days_back=None, db=Mock())

    assert response.total_analyzed == 3
    assert response.latest_model_version == "test_v1"


def test_get_sentiments_batch_endpoint_returns_values(monkeypatch):
    sentiments = [Mock(journal_id=1), Mock(journal_id=2)]
    monkeypatch.setattr(
        router_module, "get_sentiments_by_journal_ids", Mock(return_value=sentiments)
    )

    response = router_module.get_sentiments_batch_endpoint(
        journal_ids=[1, 2],
        reliable_only=False,
        db=Mock(),
    )

    assert response == sentiments


def test_get_recent_sentiments_endpoint_returns_values(monkeypatch):
    sentiments = [Mock(journal_id=1)]
    monkeypatch.setattr(router_module, "get_recent_sentiments", Mock(return_value=sentiments))

    response = router_module.get_recent_sentiments_endpoint(
        limit=5,
        reliable_only=True,
        user_id=None,
        db=Mock(),
    )

    assert response == sentiments


def test_sentiment_service_health_returns_healthy():
    client = Mock()
    client.is_ready.return_value = True
    client.get_model_info.return_value = {"model_version": "test_v1", "status": "loaded"}

    response = router_module.sentiment_service_health(sentiment_client=client)

    assert response["status"] == "healthy"
    assert response["service"] == "sentiment_analysis"


def test_sentiment_service_health_returns_503_when_unhealthy():
    client = Mock()
    client.is_ready.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        router_module.sentiment_service_health(sentiment_client=client)

    assert exc_info.value.status_code == 503
