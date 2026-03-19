from src.dependencies import get_openai_topic_client
from src.main import app


def test_extract_work_topics_openai(client_fixture, mock_openai_topic_client):
    """Test OpenAI topic extraction on a work-related journal entry."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/2/topics/openai?max_topics=5")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_extract_relationship_topics_openai(client_fixture, mock_openai_topic_client):
    """Test OpenAI topic extraction on a relationship-focused entry."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/3/topics/openai?max_topics=5")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_journal_not_found_openai(client_fixture, mock_openai_topic_client):
    """Test 404 when journal does not exist."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/99999/topics/openai")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_openai_health_endpoint(client_fixture):
    """Test OpenAI topic service health check."""
    response = client_fixture.get("/v1/health/topics/openai")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "topic_extraction_openai"


def test_custom_max_topics(client_fixture, mock_openai_topic_client):
    """Test that max_topics parameter is forwarded correctly."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/1/topics/openai?max_topics=3")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
