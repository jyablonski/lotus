from core.admin import admin_site
from core.models import FeatureFlag
from django.urls import reverse
import pytest


@pytest.mark.django_db
class TestFeatureFlagAdmin:
    def test_feature_flag_registered_in_admin(self):
        assert FeatureFlag in admin_site._registry

    def test_admin_list_view(self, admin_client):
        FeatureFlag.objects.create(flag_name="test_feature", enabled=True)
        url = reverse("lotus_admin:core_featureflag_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "test_feature" in response.content.decode()

    def test_admin_add_view(self, admin_client):
        url = reverse("lotus_admin:core_featureflag_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_admin_create_feature_flag(self, admin_client):
        url = reverse("lotus_admin:core_featureflag_add")
        data = {
            "flag_name": "new_feature",
            "enabled": True,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302

        flag = FeatureFlag.objects.get(flag_name="new_feature")
        assert flag.enabled is True

    def test_admin_edit_feature_flag(self, admin_client):
        flag = FeatureFlag.objects.create(flag_name="editable_feature", enabled=False)
        url = reverse("lotus_admin:core_featureflag_change", args=[flag.pk])
        response = admin_client.get(url)
        assert response.status_code == 200

        data = {
            "flag_name": "editable_feature",
            "enabled": True,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302

        flag.refresh_from_db()
        assert flag.enabled is True

    def test_admin_search(self, admin_client):
        FeatureFlag.objects.create(flag_name="searchable_feature", enabled=True)
        FeatureFlag.objects.create(flag_name="other_feature", enabled=False)

        url = reverse("lotus_admin:core_featureflag_changelist")
        response = admin_client.get(url, {"q": "searchable"})
        assert response.status_code == 200
        assert "searchable_feature" in response.content.decode()
        assert "other_feature" not in response.content.decode()

    def test_admin_filter_by_enabled(self, admin_client):
        FeatureFlag.objects.create(flag_name="enabled_feature", enabled=True)
        FeatureFlag.objects.create(flag_name="disabled_feature", enabled=False)

        url = reverse("lotus_admin:core_featureflag_changelist")
        response = admin_client.get(url, {"enabled__exact": "1"})
        assert response.status_code == 200
        assert "enabled_feature" in response.content.decode()
        assert "disabled_feature" not in response.content.decode()

    def test_admin_readonly_fields(self, admin_client):
        flag = FeatureFlag.objects.create(flag_name="test_feature", enabled=True)
        url = reverse("lotus_admin:core_featureflag_change", args=[flag.pk])
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "id" in content
        assert "created_at" in content
        assert "modified_at" in content

    def test_non_admin_cannot_access(self, client):
        url = reverse("lotus_admin:core_featureflag_changelist")
        response = client.get(url)
        assert response.status_code in [302, 403]
