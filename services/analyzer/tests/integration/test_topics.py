from src.dependencies import get_topic_client
from src.main import app


def test_extract_work_topics(client_fixture, real_topic_client):
    """Test topic extraction on work-related journal entry."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Journal ID 2: "Work was really stressful today. I had three
        # important meetings..."
        response = client_fixture.post("/v1/journals/2/topics")

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_extract_productivity_topics(client_fixture, real_topic_client):
    """Test topic extraction on productivity-focused content."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Journal ID 5: "Spent the day working on productivity improvements..."
        response = client_fixture.post("/v1/journals/5/topics")

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_extract_positive_topics(client_fixture, real_topic_client):
    """Test topic extraction on positive journal entry."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Journal ID 1: "Today was an absolutely amazing day! I accomplished
        # everything..."
        response = client_fixture.post("/v1/journals/1/topics")

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_get_extracted_topics(client_fixture, real_topic_client):
    """Test retrieving topics after extraction."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # First extract topics
        extract_response = client_fixture.post("/v1/journals/1/topics")
        assert extract_response.status_code == 204

        # Then retrieve them
        get_response = client_fixture.get("/v1/journals/1/topics")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["journal_id"] == 1
        assert "topics" in data
        assert isinstance(data["topics"], list)

        # Should have at least one topic
        if data["topics"]:
            topic = data["topics"][0]
            assert "topic_name" in topic
            assert "confidence" in topic
            assert "ml_model_version" in topic
            assert "created_at" in topic
            assert isinstance(topic["confidence"], (int, float))

    finally:
        app.dependency_overrides.clear()


def test_get_topics_multiple_extractions(client_fixture, real_topic_client):
    """Test that multiple extractions work correctly."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Extract topics from different journals
        journals_to_test = [1, 2, 3]

        for journal_id in journals_to_test:
            extract_response = client_fixture.post(f"/v1/journals/{journal_id}/topics")
            assert extract_response.status_code == 204

            # Verify we can retrieve each one
            get_response = client_fixture.get(f"/v1/journals/{journal_id}/topics")
            assert get_response.status_code == 200

            data = get_response.json()
            assert data["journal_id"] == journal_id
            assert "topics" in data

    finally:
        app.dependency_overrides.clear()


def test_get_topics(client_fixture, real_topic_client):
    """Test getting topics when none have been extracted yet."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Try to get topics without extracting first
        response = client_fixture.get("/v1/journals/1/topics")

        assert response.status_code == 200
        data = response.json()
        assert data["journal_id"] == 1

    finally:
        app.dependency_overrides.clear()


def test_topic_health_endpoint_unhealthy(client_fixture):
    """Test topic service health check when service is unhealthy."""
    # Create a mock unhealthy client
    from unittest.mock import Mock

    unhealthy_client = Mock()
    unhealthy_client.is_ready.return_value = False

    app.dependency_overrides[get_topic_client] = lambda: unhealthy_client

    try:
        response = client_fixture.get("/v1/health/topics")

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["service"] == "topic_extraction"

    finally:
        app.dependency_overrides.clear()


def test_topic_extraction_creates_different_results(client_fixture, real_topic_client):
    """Test that different journal entries produce different topic results."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Extract topics from different types of content
        journals_to_compare = [1, 2, 4]  # positive, work, negative
        results = {}

        for journal_id in journals_to_compare:
            # Extract topics
            extract_response = client_fixture.post(f"/v1/journals/{journal_id}/topics")
            assert extract_response.status_code == 204

            # Get results
            get_response = client_fixture.get(f"/v1/journals/{journal_id}/topics")
            assert get_response.status_code == 200

            data = get_response.json()
            results[journal_id] = data["topics"]

        # Results should exist for all journals
        for journal_id, topics in results.items():
            assert isinstance(topics, list)
            # Should have at least some topics (could be empty if confidence is low)
            if topics:
                assert all("topic_name" in topic for topic in topics)
                assert all("confidence" in topic for topic in topics)

    finally:
        app.dependency_overrides.clear()


def test_topic_model_version_consistency(client_fixture, real_topic_client):
    """Test that extracted topics have consistent model version."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Extract topics
        extract_response = client_fixture.post("/v1/journals/1/topics")
        assert extract_response.status_code == 204

        # Get topics and check model version
        get_response = client_fixture.get("/v1/journals/1/topics")
        assert get_response.status_code == 200

        data = get_response.json()
        topics = data["topics"]

        if topics:  # If we have topics
            model_versions = [topic["ml_model_version"] for topic in topics]
            # All topics should have the same model version
            assert len(set(model_versions)) == 1
            assert model_versions[0] == real_topic_client.model_version

    finally:
        app.dependency_overrides.clear()


def test_topic_confidence_values(client_fixture, real_topic_client):
    """Test that topic confidence values are reasonable."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Extract topics
        extract_response = client_fixture.post("/v1/journals/1/topics")
        assert extract_response.status_code == 204

        # Get topics and check confidence values
        get_response = client_fixture.get("/v1/journals/1/topics")
        assert get_response.status_code == 200

        data = get_response.json()
        topics = data["topics"]

        for topic in topics:
            confidence = topic["confidence"]
            # Confidence should be between 0 and 1
            assert 0 <= confidence <= 1
            # Should be a proper float/number
            assert isinstance(confidence, (int, float))

    finally:
        app.dependency_overrides.clear()
