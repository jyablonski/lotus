from datetime import datetime
from unittest.mock import Mock, patch

from src.dependencies import get_sentiment_client
from src.main import app


def test_analyze_journal_sentiment_success(
    client_fixture, mock_sentiment_client, mock_journal
):
    """Test successful sentiment analysis."""
    app.dependency_overrides[get_sentiment_client] = lambda: mock_sentiment_client

    try:
        with patch("src.routers.sentiment.Journals") as mock_journals_model:
            mock_journals_model.query.return_value.filter.return_value.first.return_value = mock_journal

            with patch("src.routers.sentiment.create_or_update_sentiment") as mock_crud:
                mock_crud.return_value = Mock(id=1, journal_id=1, sentiment="positive")

                response = client_fixture.post(
                    "/journals/1/sentiment/analyze", json={"force_reanalyze": False}
                )

                assert response.status_code == 200
                mock_sentiment_client.predict_sentiment.assert_called_once()
                mock_crud.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_analyze_journal_sentiment_journal_not_found(
    client_fixture, mock_sentiment_client
):
    """Test sentiment analysis with non-existent journal."""
    app.dependency_overrides[get_sentiment_client] = lambda: mock_sentiment_client

    try:
        with patch("src.routers.sentiment.Journals") as mock_journals_model:
            mock_journals_model.query.return_value.filter.return_value.first.return_value = None

            response = client_fixture.post(
                "/journals/999/sentiment/analyze", json={"force_reanalyze": False}
            )

            assert response.status_code == 404
            assert "Journal entry not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_analyze_journal_sentiment_force_reanalyze(
    client_fixture, mock_sentiment_client, mock_journal
):
    """Test forcing re-analysis of sentiment."""
    app.dependency_overrides[get_sentiment_client] = lambda: mock_sentiment_client

    try:
        with patch("src.routers.sentiment.Journals") as mock_journals_model:
            mock_journals_model.query.return_value.filter.return_value.first.return_value = mock_journal

            with patch("src.routers.sentiment.create_or_update_sentiment") as mock_crud:
                mock_crud.return_value = Mock(id=1, journal_id=1, sentiment="positive")

                response = client_fixture.post(
                    "/journals/1/sentiment/analyze", json={"force_reanalyze": True}
                )

                assert response.status_code == 200
                call_args = mock_crud.call_args
                assert call_args[1]["force_update"] is True
    finally:
        app.dependency_overrides.clear()


def test_get_journal_sentiment_success(client_fixture, mock_sentiment_record):
    """Test getting sentiment analysis for a journal."""
    with patch("src.routers.sentiment.get_sentiment_by_journal_id") as mock_get:
        mock_get.return_value = mock_sentiment_record

        response = client_fixture.get("/journals/1/sentiment")

        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "positive"
        assert data["confidence"] == 0.8234
        mock_get.assert_called_once()


def test_get_journal_sentiment_not_found(client_fixture):
    """Test getting sentiment when none exists."""
    with patch("src.routers.sentiment.get_sentiment_by_journal_id") as mock_get:
        mock_get.return_value = None

        response = client_fixture.get("/journals/999/sentiment")

        assert response.status_code == 404
        assert "Sentiment analysis not found" in response.json()["detail"]


def test_get_journal_sentiment_with_model_version(
    client_fixture, mock_sentiment_record
):
    """Test getting sentiment for specific model version."""
    with patch("src.routers.sentiment.get_sentiment_by_journal_id") as mock_get:
        mock_get.return_value = mock_sentiment_record

        response = client_fixture.get("/journals/1/sentiment?model_version=v1.0.0")

        assert response.status_code == 200
        mock_get.assert_called_with(
            db=mock_get.call_args[1]["db"], journal_id=1, model_version="v1.0.0"
        )


def test_update_journal_sentiment(client_fixture, mock_sentiment_client, mock_journal):
    """Test updating/re-analyzing sentiment."""
    app.dependency_overrides[get_sentiment_client] = lambda: mock_sentiment_client

    try:
        with patch("src.routers.sentiment.Journals") as mock_journals_model:
            mock_journals_model.query.return_value.filter.return_value.first.return_value = mock_journal

            with patch("src.routers.sentiment.create_or_update_sentiment") as mock_crud:
                mock_crud.return_value = Mock(id=1, journal_id=1, sentiment="positive")

                response = client_fixture.put(
                    "/journals/1/sentiment", json={"force_reanalyze": False}
                )

                assert response.status_code == 200
                # Should force reanalyze when updating
                call_args = mock_crud.call_args
                assert call_args[1]["force_update"] is True
    finally:
        app.dependency_overrides.clear()


def test_delete_journal_sentiment_success(client_fixture):
    """Test deleting sentiment analysis."""
    with patch("src.routers.sentiment.delete_sentiment") as mock_delete:
        mock_delete.return_value = 1

        response = client_fixture.delete("/journals/1/sentiment")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 1
        assert "Deleted 1 sentiment analysis record(s)" in data["message"]
        mock_delete.assert_called_once()


def test_delete_journal_sentiment_not_found(client_fixture):
    """Test deleting non-existent sentiment analysis."""
    with patch("src.routers.sentiment.delete_sentiment") as mock_delete:
        mock_delete.return_value = 0

        response = client_fixture.delete("/journals/999/sentiment")

        assert response.status_code == 404
        assert "No sentiment analysis found to delete" in response.json()["detail"]


def test_delete_journal_sentiment_with_model_version(client_fixture):
    """Test deleting sentiment for specific model version."""
    with patch("src.routers.sentiment.delete_sentiment") as mock_delete:
        mock_delete.return_value = 1

        response = client_fixture.delete("/journals/1/sentiment?model_version=v1.0.0")

        assert response.status_code == 200
        mock_delete.assert_called_with(
            db=mock_delete.call_args[1]["db"], journal_id=1, model_version="v1.0.0"
        )


def test_analyze_journals_sentiment_batch_success(
    client_fixture, mock_sentiment_client
):
    """Test batch sentiment analysis."""
    app.dependency_overrides[get_sentiment_client] = lambda: mock_sentiment_client

    try:
        mock_journals = [
            Mock(id=1, journal_text="Happy text"),
            Mock(id=2, journal_text="Sad text"),
        ]

        with patch("src.routers.sentiment.Journals") as mock_journals_model:
            mock_journals_model.query.return_value.filter.return_value.all.return_value = mock_journals

            with patch("src.routers.sentiment.create_or_update_sentiment") as mock_crud:
                mock_crud.return_value = Mock(id=1, sentiment="positive")

                response = client_fixture.post(
                    "/journals/sentiment/analyze-batch",
                    json={"journal_ids": [1, 2], "force_reanalyze": False},
                )

                assert response.status_code == 200
                assert mock_sentiment_client.predict_sentiment.call_count == 2
                assert mock_crud.call_count == 2
    finally:
        app.dependency_overrides.clear()


def test_analyze_journals_sentiment_batch_missing_journals(
    client_fixture, mock_sentiment_client
):
    """Test batch analysis with missing journals."""
    app.dependency_overrides[get_sentiment_client] = lambda: mock_sentiment_client

    try:
        with patch("src.routers.sentiment.Journals") as mock_journals_model:
            mock_journals_model.query.return_value.filter.return_value.all.return_value = []

            response = client_fixture.post(
                "/journals/sentiment/analyze-batch",
                json={"journal_ids": [999, 1000], "force_reanalyze": False},
            )

            assert response.status_code == 404
            assert "Journal entries not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_sentiment_trends_success(client_fixture):
    """Test getting sentiment trends."""
    mock_trends = [
        {
            "period": "2024-01-08",
            "sentiment_counts": {
                "positive": 5,
                "negative": 2,
                "neutral": 3,
                "uncertain": 0,
            },
            "avg_confidence": 0.7654,
            "total_entries": 10,
            "dominant_sentiment": "positive",
        }
    ]

    with patch("src.routers.sentiment.get_sentiment_trends") as mock_get_trends:
        mock_get_trends.return_value = mock_trends

        response = client_fixture.get(
            "/journals/sentiment/trends?days_back=30&group_by=week"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["dominant_sentiment"] == "positive"
        assert data[0]["total_entries"] == 10


def test_get_sentiment_trends_invalid_group_by(client_fixture):
    """Test sentiment trends with invalid group_by parameter."""
    response = client_fixture.get("/journals/sentiment/trends?group_by=invalid")

    assert response.status_code == 400
    assert "group_by must be 'day', 'week', or 'month'" in response.json()["detail"]


def test_get_sentiment_stats_success(client_fixture):
    """Test getting sentiment statistics."""
    mock_stats = {
        "total_analyzed": 150,
        "reliable_count": 142,
        "reliability_rate": 0.9467,
        "sentiment_distribution": {
            "positive": 75,
            "negative": 35,
            "neutral": 32,
            "uncertain": 8,
        },
        "avg_confidence": 0.7234,
        "latest_model_version": "v1.0.0",
    }

    with patch("src.routers.sentiment.get_sentiment_stats") as mock_get_stats:
        mock_get_stats.return_value = mock_stats

        response = client_fixture.get("/journals/sentiment/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] == 150
        assert data["reliability_rate"] == 0.9467
        assert data["latest_model_version"] == "v1.0.0"


def test_get_sentiment_stats_no_data(client_fixture):
    """Test getting sentiment statistics when no data exists."""
    mock_stats = {"total_analyzed": 0}

    with patch("src.routers.sentiment.get_sentiment_stats") as mock_get_stats:
        mock_get_stats.return_value = mock_stats

        response = client_fixture.get("/journals/sentiment/stats")

        assert response.status_code == 404
        assert "No sentiment analysis data found" in response.json()["detail"]


def test_get_sentiments_batch_success(client_fixture):
    """Test getting multiple sentiments."""
    mock_sentiments = [
        Mock(id=1, journal_id=1, sentiment="positive"),
        Mock(id=2, journal_id=2, sentiment="negative"),
    ]

    with patch("src.routers.sentiment.get_sentiments_by_journal_ids") as mock_get_batch:
        mock_get_batch.return_value = mock_sentiments

        response = client_fixture.get(
            "/journals/sentiment/batch?journal_ids=1&journal_ids=2"
        )

        assert response.status_code == 200
        mock_get_batch.assert_called_once()


def test_get_recent_sentiments_success(client_fixture):
    """Test getting recent sentiment analyses."""
    mock_sentiments = [Mock(id=1, sentiment="positive", created_at=datetime.now())]

    with patch("src.routers.sentiment.get_recent_sentiments") as mock_get_recent:
        mock_get_recent.return_value = mock_sentiments

        response = client_fixture.get("/journals/sentiment/recent?limit=10")

        assert response.status_code == 200
        mock_get_recent.assert_called_with(
            db=mock_get_recent.call_args[1]["db"],
            limit=10,
            reliable_only=True,
            user_id=None,
        )
