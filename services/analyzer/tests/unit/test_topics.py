from src.dependencies import get_topic_client
from src.main import app


def test_extract_topics_endpoint(client_fixture, mock_topic_client):
    """Test topic extraction endpoint."""
    # Override the dependency directly
    app.dependency_overrides[get_topic_client] = lambda: mock_topic_client

    try:
        response = client_fixture.post("/v1/journals/1/topics")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_get_topics_endpoint(client_fixture):
    """Test getting topics endpoint."""
    response = client_fixture.get("/v1/journals/1/topics")
    assert response.status_code == 200


def test_health_topics_endpoint(client_fixture, mock_topic_client):
    """Test health endpoint."""

    app.dependency_overrides[get_topic_client] = lambda: mock_topic_client

    try:
        response = client_fixture.get("/v1/health/topics")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
