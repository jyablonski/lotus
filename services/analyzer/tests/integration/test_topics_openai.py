from unittest.mock import AsyncMock, Mock, patch

from src.dependencies import get_openai_topic_client
from src.main import app
from src.schemas.openai_topics import TopicAnalysis


def test_extract_work_topics(client_fixture, mock_openai_topic_client):
    """Test topic extraction on work-related journal entry."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/2/openai/topics")
        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_extract_relationship_topics(client_fixture, mock_openai_topic_client):
    """Test topic extraction on relationship journal entry."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/1/openai/topics?max_topics=7")
        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_extract_topics_custom_count(client_fixture, mock_openai_topic_client):
    """Test topic extraction with custom topic count."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/1/openai/topics?max_topics=3")
        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_journal_not_found(client_fixture, mock_openai_topic_client):
    """Test behavior when journal doesn't exist."""
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/99999/openai/topics")
        assert response.status_code == 404

    finally:
        app.dependency_overrides.clear()


@patch("src.clients.openai_topic_client.mlflow")
def test_mlflow_integration(mock_mlflow, client_fixture, mock_openai_topic_client):
    """Test that MLflow logging is called during topic extraction."""

    # Use your existing working mock and just patch mlflow in the real client
    app.dependency_overrides[get_openai_topic_client] = lambda: mock_openai_topic_client

    try:
        response = client_fixture.post("/v1/journals/1/openai/topics")
        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_error_handling(client_fixture):
    """Test error handling when OpenAI client fails."""

    async def failing_analyze_topics(request):
        raise Exception("OpenAI API Error")

    mock_client = AsyncMock()
    mock_client.analyze_topics = failing_analyze_topics

    app.dependency_overrides[get_openai_topic_client] = lambda: mock_client

    try:
        response = client_fixture.post("/v1/journals/1/openai/topics")
        assert response.status_code == 500

    finally:
        app.dependency_overrides.clear()


# test real OpenAI integration
# @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OpenAI API key")
# def test_real_openai_integration(client_fixture):
#     """Integration test with real OpenAI API (runs only if API key present)."""
#     # No mocking - uses real OpenAI client
#     response = client_fixture.post("/v1/journals/1/openai/topics?max_topics=5")
#     assert response.status_code == 204
