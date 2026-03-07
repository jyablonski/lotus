from core.admin import admin_site
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
