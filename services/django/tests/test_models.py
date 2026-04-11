from datetime import date

from core.models import (
    CommunityMoodRollup,
    CommunityPromptSet,
    CommunitySummary,
    CommunityThemeRollup,
    Journal,
    JournalCommunityProjection,
    JournalContentFlag,
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

    def test_user_community_fields_default_correctly(self):
        user = User.objects.create(email="community-defaults@example.com")

        assert user.community_insights_opt_in is False
        assert user.community_location_opt_in is False
        assert user.community_country_code is None
        assert user.community_region_code is None


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
class TestJournalContentFlag:
    def test_journal_content_flag_str(self):
        user = User.objects.create(email="test@example.com")
        journal = Journal.objects.create(user=user, journal_text="Test entry")
        content_flag = JournalContentFlag.objects.create(
            journal=journal,
            flag_type="crisis",
            severity="high",
            matched_terms=["self-harm"],
            analysis_summary="Detected crisis-oriented language.",
        )
        assert "crisis" in str(content_flag)
        assert "high" in str(content_flag)


@pytest.mark.django_db
class TestJournalCommunityProjection:
    def test_projection_str_is_informative(self):
        user = User.objects.create(email="projection@example.com")
        journal = Journal.objects.create(user=user, journal_text="Community-ready entry")

        projection = JournalCommunityProjection.objects.create(
            journal=journal,
            user=user,
            eligible_for_community=True,
            entry_local_date=date(2026, 4, 7),
            primary_mood="hopeful",
            primary_sentiment="positive",
            theme_names=["growth", "connection"],
            analysis_version="v1",
        )

        assert str(projection) == f"Community projection for Journal {journal.id}"


@pytest.mark.django_db
class TestCommunityRollups:
    def test_rollup_models_can_be_created(self):
        theme_rollup = CommunityThemeRollup.objects.create(
            bucket_date=date(2026, 4, 7),
            time_grain="day",
            scope_type="global",
            scope_value="global",
            theme_name="connection",
            entry_count=12,
            unique_user_count=10,
            rank=1,
        )
        mood_rollup = CommunityMoodRollup.objects.create(
            bucket_date=date(2026, 4, 7),
            time_grain="day",
            scope_type="region",
            scope_value="US-CA",
            mood_name="hopeful",
            entry_count=9,
            unique_user_count=8,
            rank=2,
        )
        summary = CommunitySummary.objects.create(
            bucket_date=date(2026, 4, 7),
            time_grain="day",
            scope_type="global",
            scope_value="global",
            summary_text="People are feeling more connected today.",
            source_theme_names=["connection"],
            source_mood_names=["hopeful"],
        )

        assert theme_rollup.pk is not None
        assert mood_rollup.pk is not None
        assert summary.pk is not None


@pytest.mark.django_db
class TestCommunityPromptSet:
    def test_prompt_set_json_persists_expected_structure(self):
        prompt_set = CommunityPromptSet.objects.create(
            bucket_date=date(2026, 4, 7),
            time_grain="day",
            scope_type="global",
            scope_value="global",
            prompt_set_json=[
                {
                    "title": "Small step",
                    "prompt": "What is one kind thing you can do for yourself today?",
                }
            ],
            source_theme_names=["self-care"],
            source_mood_names=["steady"],
        )

        prompt_set.refresh_from_db()

        assert prompt_set.prompt_set_json == [
            {
                "title": "Small step",
                "prompt": "What is one kind thing you can do for yourself today?",
            }
        ]
