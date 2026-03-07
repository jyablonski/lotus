from core.models import (
    Journal,
    JournalDetail,
    JournalSentiment,
    JournalTopic,
    User,
)
import pytest


@pytest.mark.django_db
class TestUser:
    def test_user_str(self):
        user = User.objects.create(email="test@example.com", role="Consumer")
        assert str(user) == "test@example.com"

    def test_user_is_admin_true(self):
        user = User.objects.create(email="admin@example.com", role="Admin")
        assert user.is_admin is True

    def test_user_is_admin_false(self):
        user = User.objects.create(email="user@example.com", role="Consumer")
        assert user.is_admin is False


@pytest.mark.django_db
class TestJournal:
    def test_journal_str(self):
        user = User.objects.create(email="test@example.com")
        journal = Journal.objects.create(user=user, journal_text="Test entry")
        assert "Journal" in str(journal)
        assert "test@example.com" in str(journal)


@pytest.mark.django_db
class TestJournalDetail:
    def test_journal_detail_str(self):
        user = User.objects.create(email="test@example.com")
        journal = Journal.objects.create(user=user, journal_text="Test entry")
        detail = JournalDetail.objects.create(journal=journal, sentiment_score=0.8)
        assert "Details for Journal" in str(detail)


@pytest.mark.django_db
class TestJournalTopic:
    def test_journal_topic_str(self):
        user = User.objects.create(email="test@example.com")
        journal = Journal.objects.create(user=user, journal_text="Test entry")
        topic = JournalTopic.objects.create(
            journal=journal,
            topic_name="happiness",
            confidence=0.85,
            ml_model_version="v1.0",
        )
        assert "happiness" in str(topic)
        assert "0.85" in str(topic)


@pytest.mark.django_db
class TestJournalSentiment:
    def test_journal_sentiment_str(self):
        user = User.objects.create(email="test@example.com")
        journal = Journal.objects.create(user=user, journal_text="Test entry")
        sentiment = JournalSentiment.objects.create(
            journal=journal,
            sentiment="positive",
            confidence=0.9,
            confidence_level="high",
            ml_model_version="v1.0",
        )
        assert "positive" in str(sentiment)
        assert "high" in str(sentiment)
