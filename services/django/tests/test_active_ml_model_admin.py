from core.admin import admin_site, has_ml_model_permission
from core.models import (
    ActiveMLModel,
    User as LotusUser,
)
from django.contrib.auth.models import (
    Group,
    User as DjangoUser,
)
from django.urls import reverse
import pytest


@pytest.mark.django_db
class TestActiveMLModelAdmin:
    def test_active_ml_model_registered_in_admin(self):
        assert ActiveMLModel in admin_site._registry

    def test_admin_can_view_list(self, admin_client):
        ActiveMLModel.objects.create(ml_model="sentiment_analyzer", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "sentiment_analyzer" in response.content.decode()

    def test_admin_can_add(self, admin_client):
        url = reverse("lotus_admin:core_activemlmodel_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_admin_can_create(self, admin_client):
        url = reverse("lotus_admin:core_activemlmodel_add")
        data = {
            "ml_model": "new_model",
            "is_enabled": True,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302

        model = ActiveMLModel.objects.get(ml_model="new_model")
        assert model.is_enabled is True

    def test_admin_can_edit(self, admin_client):
        model = ActiveMLModel.objects.create(ml_model="editable_model", is_enabled=False)
        url = reverse("lotus_admin:core_activemlmodel_change", args=[model.pk])
        response = admin_client.get(url)
        assert response.status_code == 200

        data = {
            "ml_model": "editable_model",
            "is_enabled": True,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302

        model.refresh_from_db()
        assert model.is_enabled is True

    def test_admin_can_delete(self, admin_client):
        model = ActiveMLModel.objects.create(ml_model="deletable_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_delete", args=[model.pk])
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(url, {"post": "yes"})
        assert response.status_code == 302
        assert not ActiveMLModel.objects.filter(ml_model="deletable_model").exists()

    def test_product_manager_group_can_view_list(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create product_manager group
        group, _ = Group.objects.get_or_create(name="product_manager")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="pm_user",
            email="pm@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="pm@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        ActiveMLModel.objects.create(ml_model="test_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_changelist")
        response = client.get(url)
        assert response.status_code == 200
        assert "test_model" in response.content.decode()

    def test_product_manager_group_can_add(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create product_manager group
        group, _ = Group.objects.get_or_create(name="product_manager")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="pm_user2",
            email="pm2@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="pm2@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        url = reverse("lotus_admin:core_activemlmodel_add")
        response = client.get(url)
        assert response.status_code == 200

    def test_product_manager_group_can_create(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create product_manager group
        group, _ = Group.objects.get_or_create(name="product_manager")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="pm_user3",
            email="pm3@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="pm3@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        url = reverse("lotus_admin:core_activemlmodel_add")
        data = {
            "ml_model": "pm_created_model",
            "is_enabled": True,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        model = ActiveMLModel.objects.get(ml_model="pm_created_model")
        assert model.is_enabled is True

    def test_product_manager_group_can_edit(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create product_manager group
        group, _ = Group.objects.get_or_create(name="product_manager")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="pm_user4",
            email="pm4@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="pm4@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        model = ActiveMLModel.objects.create(ml_model="pm_editable_model", is_enabled=False)
        url = reverse("lotus_admin:core_activemlmodel_change", args=[model.pk])
        response = client.get(url)
        assert response.status_code == 200

        data = {
            "ml_model": "pm_editable_model",
            "is_enabled": True,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        model.refresh_from_db()
        assert model.is_enabled is True

    def test_product_manager_group_can_delete(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create product_manager group
        group, _ = Group.objects.get_or_create(name="product_manager")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="pm_user5",
            email="pm5@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="pm5@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        model = ActiveMLModel.objects.create(ml_model="pm_deletable_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_delete", args=[model.pk])
        response = client.get(url)
        assert response.status_code == 200

        response = client.post(url, {"post": "yes"})
        assert response.status_code == 302
        assert not ActiveMLModel.objects.filter(ml_model="pm_deletable_model").exists()

    def test_ml_engineer_group_can_view_list(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create ml_engineer group
        group, _ = Group.objects.get_or_create(name="ml_engineer")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="ml_user",
            email="ml@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="ml@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        ActiveMLModel.objects.create(ml_model="test_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_changelist")
        response = client.get(url)
        assert response.status_code == 200
        assert "test_model" in response.content.decode()

    def test_ml_engineer_group_can_add(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create ml_engineer group
        group, _ = Group.objects.get_or_create(name="ml_engineer")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="ml_user2",
            email="ml2@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="ml2@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        url = reverse("lotus_admin:core_activemlmodel_add")
        response = client.get(url)
        assert response.status_code == 200

    def test_ml_engineer_group_can_create(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create ml_engineer group
        group, _ = Group.objects.get_or_create(name="ml_engineer")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="ml_user3",
            email="ml3@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="ml3@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        url = reverse("lotus_admin:core_activemlmodel_add")
        data = {
            "ml_model": "ml_created_model",
            "is_enabled": True,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        model = ActiveMLModel.objects.get(ml_model="ml_created_model")
        assert model.is_enabled is True

    def test_ml_engineer_group_can_edit(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create ml_engineer group
        group, _ = Group.objects.get_or_create(name="ml_engineer")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="ml_user4",
            email="ml4@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="ml4@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        model = ActiveMLModel.objects.create(ml_model="ml_editable_model", is_enabled=False)
        url = reverse("lotus_admin:core_activemlmodel_change", args=[model.pk])
        response = client.get(url)
        assert response.status_code == 200

        data = {
            "ml_model": "ml_editable_model",
            "is_enabled": True,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        model.refresh_from_db()
        assert model.is_enabled is True

    def test_ml_engineer_group_can_delete(self, client):
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create ml_engineer group
        group, _ = Group.objects.get_or_create(name="ml_engineer")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="ml_user5",
            email="ml5@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="ml5@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        model = ActiveMLModel.objects.create(ml_model="ml_deletable_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_delete", args=[model.pk])
        response = client.get(url)
        assert response.status_code == 200

        response = client.post(url, {"post": "yes"})
        assert response.status_code == 302
        assert not ActiveMLModel.objects.filter(ml_model="ml_deletable_model").exists()

    def test_regular_user_cannot_access(self, client):
        # Create Django user without Admin role and not in product_manager group
        django_user = DjangoUser.objects.create_user(
            username="regular_user",
            email="regular@test.com",
            password="testpass123",
        )

        # Create matching LotusUser with Consumer role
        LotusUser.objects.get_or_create(
            email="regular@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        url = reverse("lotus_admin:core_activemlmodel_changelist")
        response = client.get(url)
        # Should be forbidden or redirected
        assert response.status_code in [302, 403]

    def test_regular_user_cannot_add(self, client):
        # Create Django user without Admin role and not in product_manager group
        django_user = DjangoUser.objects.create_user(
            username="regular_user2",
            email="regular2@test.com",
            password="testpass123",
        )

        # Create matching LotusUser with Consumer role
        LotusUser.objects.get_or_create(
            email="regular2@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        url = reverse("lotus_admin:core_activemlmodel_add")
        response = client.get(url)
        # Should be forbidden or redirected
        assert response.status_code in [302, 403]

    def test_regular_user_cannot_edit(self, client):
        # Create Django user without Admin role and not in product_manager group
        django_user = DjangoUser.objects.create_user(
            username="regular_user3",
            email="regular3@test.com",
            password="testpass123",
        )

        # Create matching LotusUser with Consumer role
        LotusUser.objects.get_or_create(
            email="regular3@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        client.force_login(django_user)

        model = ActiveMLModel.objects.create(ml_model="protected_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_change", args=[model.pk])
        response = client.get(url)
        # Should be forbidden or redirected
        assert response.status_code in [302, 403]

    def test_has_ml_model_permission_admin_role(self, admin_user):
        """Test that has_ml_model_permission returns True for Admin role users."""
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()
        assert has_ml_model_permission(admin_user) is True

    def test_has_ml_model_permission_product_manager_group(self, db):
        """Test that has_ml_model_permission returns True for product_manager group users."""
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create product_manager group
        group, _ = Group.objects.get_or_create(name="product_manager")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="pm_test",
            email="pm_test@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="pm_test@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        assert has_ml_model_permission(django_user) is True

    def test_has_ml_model_permission_ml_engineer_group(self, db):
        """Test that has_ml_model_permission returns True for ml_engineer group users."""
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create ml_engineer group
        group, _ = Group.objects.get_or_create(name="ml_engineer")

        # Create Django user
        django_user = DjangoUser.objects.create_user(
            username="ml_test",
            email="ml_test@test.com",
            password="testpass123",
        )
        django_user.groups.add(group)
        django_user.save()

        # Create matching LotusUser with non-Admin role
        LotusUser.objects.get_or_create(
            email="ml_test@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        assert has_ml_model_permission(django_user) is True

    def test_has_ml_model_permission_regular_user(self, db):
        """Test that has_ml_model_permission returns False for regular users."""
        from django.core.cache import cache

        # Clear cache to ensure fresh check
        cache.clear()

        # Create Django user without Admin role and not in product_manager group
        django_user = DjangoUser.objects.create_user(
            username="regular_test",
            email="regular_test@test.com",
            password="testpass123",
        )

        # Create matching LotusUser with Consumer role
        LotusUser.objects.get_or_create(
            email="regular_test@test.com",
            defaults={"role": "Consumer", "timezone": "UTC"},
        )

        assert has_ml_model_permission(django_user) is False

    def test_admin_readonly_fields(self, admin_client):
        model = ActiveMLModel.objects.create(ml_model="test_model", is_enabled=True)
        url = reverse("lotus_admin:core_activemlmodel_change", args=[model.pk])
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "id" in content or "Id" in content
        assert "Created at" in content or "created_at" in content
        assert "Modified at" in content or "modified_at" in content
