from src.dependencies import get_sentiment_client
from src.main import app


def test_analyze_positive_sentiment(client_fixture, real_sentiment_client):
    """Test sentiment analysis on clearly positive journal entry."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        response = client_fixture.post(
            "/v1/journals/1/sentiment/analyze", json={"force_reanalyze": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "positive"
        assert data["confidence"] > 0.5  # Should be confident about clearly positive text
        assert data["is_reliable"] is True

    finally:
        app.dependency_overrides.clear()


def test_analyze_neutral_sentiment(client_fixture, real_sentiment_client):
    """Test sentiment analysis on neutral journal entry."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        response = client_fixture.post(
            "/v1/journals/3/sentiment/analyze", json={"force_reanalyze": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] in [
            "neutral",
            "positive",
        ]  # Could be either for peaceful content
        assert data["journal_id"] == 3

    finally:
        app.dependency_overrides.clear()


def test_get_sentiment_analysis(client_fixture, real_sentiment_client):
    """Test retrieving existing sentiment analysis."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        client_fixture.post("/v1/journals/1/sentiment/analyze", json={"force_reanalyze": False})

        response = client_fixture.get("/v1/journals/1/sentiment")

        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
        assert data["journal_id"] == 1

    finally:
        app.dependency_overrides.clear()


def test_force_reanalyze_sentiment(client_fixture, real_sentiment_client):
    """Test force re-analyzing sentiment."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        response1 = client_fixture.post(
            "/v1/journals/1/sentiment/analyze", json={"force_reanalyze": False}
        )
        assert response1.status_code == 200
        first_analysis_time = response1.json()["created_at"]

        response2 = client_fixture.post(
            "/v1/journals/1/sentiment/analyze", json={"force_reanalyze": True}
        )
        assert response2.status_code == 200
        second_analysis_time = response2.json()["created_at"]

        assert second_analysis_time >= first_analysis_time

    finally:
        app.dependency_overrides.clear()


def test_batch_sentiment_analysis(client_fixture, real_sentiment_client):
    """Test analyzing multiple journals at once."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        response = client_fixture.post(
            "/v1/journals/sentiment/analyze-batch",
            json={"journal_ids": [1, 2, 3], "force_reanalyze": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # All should have sentiment analysis
        for analysis in data:
            assert "sentiment" in analysis
            assert "confidence" in analysis
            assert analysis["journal_id"] in [1, 2, 3]

    finally:
        app.dependency_overrides.clear()


def test_sentiment_trends(client_fixture, real_sentiment_client):
    """Test getting sentiment trends after analyzing some entries."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        # Analyze a few entries first
        client_fixture.post(
            "/v1/journals/sentiment/analyze-batch",
            json={"journal_ids": [1, 2, 4], "force_reanalyze": False},
        )

        # Get trends
        response = client_fixture.get("/v1/journals/sentiment/trends?days_back=1&group_by=day")

        assert response.status_code == 200
        data = response.json()

        if data:  # Might be empty if no data in time range
            trend = data[0]
            assert "sentiment_counts" in trend
            assert "dominant_sentiment" in trend
            assert "total_entries" in trend

    finally:
        app.dependency_overrides.clear()


def test_sentiment_stats(client_fixture, real_sentiment_client):
    """Test getting sentiment statistics after analyzing entries."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        client_fixture.post(
            "/v1/journals/sentiment/analyze-batch",
            json={"journal_ids": [1, 2, 3, 4], "force_reanalyze": False},
        )

        response = client_fixture.get("/v1/journals/sentiment/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] >= 4
        assert "sentiment_distribution" in data
        assert "avg_confidence" in data
        assert "reliability_rate" in data

    finally:
        app.dependency_overrides.clear()


def test_nonexistent_journal_analysis(client_fixture, real_sentiment_client):
    """Test analyzing non-existent journal."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        response = client_fixture.post(
            "/v1/journals/999/sentiment/analyze", json={"force_reanalyze": False}
        )

        assert response.status_code == 404
        assert "this doesn't exist hoe" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


def test_delete_sentiment_analysis(client_fixture, real_sentiment_client):
    """Test deleting sentiment analysis."""
    app.dependency_overrides[get_sentiment_client] = lambda: real_sentiment_client

    try:
        client_fixture.post("/v1/journals/1/sentiment/analyze", json={"force_reanalyze": False})

        response = client_fixture.delete("/v1/journals/1/sentiment")

        assert response.status_code == 200
        assert response.json()["deleted_count"] == 2

        get_response = client_fixture.get("/v1/journals/1/sentiment")
        assert get_response.status_code == 404

    finally:
        app.dependency_overrides.clear()
