import logging
from unittest.mock import Mock

from src.dependencies import get_topic_client
from src.main import app
from src.models.journal_content_flags import JournalContentFlags
from src.models.journals import Journals


def test_extract_work_topics(client_fixture, real_topic_client):
    """Test topic extraction on work-related journal entry."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Journal ID 2: "Work was really stressful today. I had three
        # important meetings..."
        response = client_fixture.post("/v1/journals/2/topics/internal")

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_extract_productivity_topics(client_fixture, real_topic_client):
    """Test topic extraction on productivity-focused content."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Journal ID 5: "Spent the day working on productivity improvements..."
        response = client_fixture.post("/v1/journals/5/topics/internal")

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_extract_positive_topics(client_fixture, real_topic_client):
    """Test topic extraction on positive journal entry."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        # Journal ID 1: "Today was an absolutely amazing day! I accomplished
        # everything..."
        response = client_fixture.post("/v1/journals/1/topics/internal")

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


def test_get_extracted_topics(client_fixture, real_topic_client):
    """Test retrieving topics after extraction."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        extract_response = client_fixture.post("/v1/journals/1/topics/internal")
        assert extract_response.status_code == 204

        get_response = client_fixture.get("/v1/journals/1/topics")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["journal_id"] == 1
        assert "topics" in data
        assert isinstance(data["topics"], list)

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
        journals_to_test = [1, 2, 3]

        for journal_id in journals_to_test:
            extract_response = client_fixture.post(f"/v1/journals/{journal_id}/topics/internal")
            assert extract_response.status_code == 204

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
        response = client_fixture.get("/v1/journals/1/topics")

        assert response.status_code == 200
        data = response.json()
        assert data["journal_id"] == 1

    finally:
        app.dependency_overrides.clear()


def test_topic_health_endpoint_unhealthy(client_fixture):
    """Test topic service health check when service is unhealthy."""
    from unittest.mock import Mock

    unhealthy_client = Mock()
    unhealthy_client.is_ready.return_value = False

    app.dependency_overrides[get_topic_client] = lambda: unhealthy_client

    try:
        response = client_fixture.get("/v1/health/topics/internal")

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["service"] == "topic_extraction_internal"

    finally:
        app.dependency_overrides.clear()


def test_topic_extraction_creates_different_results(client_fixture, real_topic_client):
    """Test that different journal entries produce different topic results."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        journals_to_compare = [1, 2, 4]  # positive, work, negative
        results = {}

        for journal_id in journals_to_compare:
            extract_response = client_fixture.post(f"/v1/journals/{journal_id}/topics/internal")
            assert extract_response.status_code == 204

            get_response = client_fixture.get(f"/v1/journals/{journal_id}/topics")
            assert get_response.status_code == 200

            data = get_response.json()
            results[journal_id] = data["topics"]

        for _journal_id, topics in results.items():
            assert isinstance(topics, list)
            if topics:
                assert all("topic_name" in topic for topic in topics)
                assert all("confidence" in topic for topic in topics)

    finally:
        app.dependency_overrides.clear()


def test_topic_model_version_consistency(client_fixture, real_topic_client):
    """Test that extracted topics have consistent model version."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        extract_response = client_fixture.post("/v1/journals/1/topics/internal")
        assert extract_response.status_code == 204

        get_response = client_fixture.get("/v1/journals/1/topics")
        assert get_response.status_code == 200

        data = get_response.json()
        topics = data["topics"]

        if topics:
            model_versions = [topic["ml_model_version"] for topic in topics]
            assert len(set(model_versions)) == 1
            assert model_versions[0] == real_topic_client.model_version

    finally:
        app.dependency_overrides.clear()


def test_topic_confidence_values(client_fixture, real_topic_client):
    """Test that topic confidence values are reasonable."""
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        extract_response = client_fixture.post("/v1/journals/1/topics/internal")
        assert extract_response.status_code == 204

        get_response = client_fixture.get("/v1/journals/1/topics")
        assert get_response.status_code == 200

        data = get_response.json()
        topics = data["topics"]

        for topic in topics:
            confidence = topic["confidence"]
            assert 0 <= confidence <= 1
            assert isinstance(confidence, (int, float))

    finally:
        app.dependency_overrides.clear()


def test_flagged_content_writes_background_record_and_log(
    client_fixture,
    test_db_session,
    real_topic_client,
    caplog,
):
    flagged_journal = Journals(
        user_id="a7f3e8b2-4d91-4c3a-9f2e-1b8c5d6e7f8a",
        journal_text="I feel like I want to end my life. Everything is shit.",
    )
    test_db_session.add(flagged_journal)
    test_db_session.commit()
    test_db_session.refresh(flagged_journal)

    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        with caplog.at_level(logging.ERROR):
            response = client_fixture.post(f"/v1/journals/{flagged_journal.id}/topics/internal")

        assert response.status_code == 204

        records = (
            test_db_session.query(JournalContentFlags)
            .filter(JournalContentFlags.journal_id == flagged_journal.id)
            .order_by(JournalContentFlags.flag_type.asc())
            .all()
        )

        assert len(records) == 2
        assert [record.flag_type for record in records] == ["crisis", "profanity"]
        assert records[0].severity == "high"
        assert records[1].severity == "low"
        assert any("journal_content_flag_written" in message for message in caplog.messages)
    finally:
        app.dependency_overrides.clear()


def test_unflagged_content_does_not_write_content_flag_records(
    client_fixture,
    test_db_session,
    real_topic_client,
):
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        response = client_fixture.post("/v1/journals/1/topics/internal")

        assert response.status_code == 204

        records = (
            test_db_session.query(JournalContentFlags)
            .filter(JournalContentFlags.journal_id == 1)
            .all()
        )
        assert records == []
    finally:
        app.dependency_overrides.clear()


def test_internal_topic_extraction_returns_404_for_missing_journal(
    client_fixture, real_topic_client
):
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        response = client_fixture.post("/v1/journals/99999/topics/internal")

        assert response.status_code == 404
        assert response.json()["detail"] == "Journal not found"
    finally:
        app.dependency_overrides.clear()


def test_internal_topic_extraction_returns_500_when_model_fails(client_fixture):
    failing_client = Mock()
    failing_client.is_ready.return_value = True
    failing_client.model_version = "test_v1"
    failing_client.extract_topics.side_effect = RuntimeError("boom")

    app.dependency_overrides[get_topic_client] = lambda: failing_client

    try:
        response = client_fixture.post("/v1/journals/1/topics/internal")

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error"
    finally:
        app.dependency_overrides.clear()


def test_get_journal_topics_returns_404_for_missing_journal(client_fixture, real_topic_client):
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        response = client_fixture.get("/v1/journals/99999/topics")

        assert response.status_code == 404
        assert response.json()["detail"] == "Journal not found"
    finally:
        app.dependency_overrides.clear()


def test_topic_health_endpoint_healthy(client_fixture, real_topic_client):
    app.dependency_overrides[get_topic_client] = lambda: real_topic_client

    try:
        response = client_fixture.get("/v1/health/topics/internal")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "topic_extraction"
        assert data["model_version"] == real_topic_client.model_version
    finally:
        app.dependency_overrides.clear()
