from core.admin import admin_site
from core.models import Journal, JournalContentFlag, User
from django.urls import reverse
import pytest
from waffle.models import Flag


@pytest.mark.django_db
class TestWaffleFlagAdmin:
    def test_waffle_flag_registered_in_admin(self):
        assert Flag in admin_site._registry

    def test_admin_list_view(self, admin_client):
        Flag.objects.create(name="test_flag")
        url = reverse("lotus_admin:waffle_flag_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "test_flag" in response.content.decode()

    def test_admin_add_view(self, admin_client):
        url = reverse("lotus_admin:waffle_flag_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_non_admin_cannot_access(self, client):
        url = reverse("lotus_admin:waffle_flag_changelist")
        response = client.get(url)
        assert response.status_code in [302, 403]


@pytest.mark.django_db
class TestJournalContentFlagAdmin:
    def test_journal_content_flag_registered_in_admin(self):
        assert JournalContentFlag in admin_site._registry

    def test_content_flag_list_view(self, admin_client):
        user = User.objects.create(email="flagged@example.com")
        journal = Journal.objects.create(user=user, journal_text="Test entry")
        JournalContentFlag.objects.create(
            journal=journal,
            flag_type="profanity",
            severity="low",
            matched_terms=["damn"],
            analysis_summary="Detected profane language.",
        )

        url = reverse("lotus_admin:core_journalcontentflag_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "profanity" in response.content.decode()
