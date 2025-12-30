import uuid

from core.models import (
    FeatureFlag,
    Journal,
    JournalDetail,
    JournalSentiment,
    JournalTopic,
    User,
)
import django.db
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


@pytest.mark.django_db
class TestFeatureFlag:
    def test_create_feature_flag(self):
        flag = FeatureFlag.objects.create(
            flag_name="test_feature",
            enabled=True,
        )
        assert flag.id is not None
        assert isinstance(flag.id, uuid.UUID)
        assert flag.flag_name == "test_feature"
        assert flag.enabled is True
        assert flag.created_at is not None
        assert flag.modified_at is not None

    def test_feature_flag_default_enabled_false(self):
        flag = FeatureFlag.objects.create(flag_name="disabled_feature")
        assert flag.enabled is False

    def test_feature_flag_unique_name(self):
        FeatureFlag.objects.create(flag_name="unique_feature", enabled=True)
        with pytest.raises(django.db.IntegrityError, match="unique constraint"):
            FeatureFlag.objects.create(flag_name="unique_feature", enabled=False)

    def test_feature_flag_str_representation_enabled(self):
        flag = FeatureFlag.objects.create(flag_name="enabled_feature", enabled=True)
        assert "✓" in str(flag)
        assert "enabled_feature" in str(flag)

    def test_feature_flag_str_representation_disabled(self):
        flag = FeatureFlag.objects.create(flag_name="disabled_feature", enabled=False)
        assert "✗" in str(flag)
        assert "disabled_feature" in str(flag)

    def test_feature_flag_ordering(self):
        # Clear any existing flags to ensure clean test
        FeatureFlag.objects.all().delete()

        FeatureFlag.objects.create(flag_name="zebra", enabled=True)
        FeatureFlag.objects.create(flag_name="alpha", enabled=True)
        FeatureFlag.objects.create(flag_name="beta", enabled=True)

        flags = list(FeatureFlag.objects.all())
        assert flags[0].flag_name == "alpha"
        assert flags[1].flag_name == "beta"
        assert flags[2].flag_name == "zebra"

    def test_feature_flag_update_modified_at(self):
        flag = FeatureFlag.objects.create(flag_name="test_feature", enabled=True)
        original_modified = flag.modified_at

        flag.enabled = False
        flag.save()

        flag.refresh_from_db()
        assert flag.modified_at > original_modified
