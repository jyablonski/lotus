"""
Tests for Django User synchronization signals.
"""

from django.contrib.auth.models import User as DjangoUser
from django.test import override_settings
import pytest

from core.models import User as LotusUser


@pytest.mark.django_db
class TestSyncDjangoUserSignal:
    """Tests for sync_django_user signal (post_save)."""

    def test_create_lotus_user_with_admin_role_creates_django_user_with_admin_privileges(
        self,
    ):
        """Creating a LotusUser with Admin role should create Django User with is_staff=True and is_superuser=True."""
        lotus_user = LotusUser.objects.create(
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="admin@test.com")
        assert django_user.email == "admin@test.com"
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

    def test_create_lotus_user_with_consumer_role_creates_django_user_without_admin_privileges(
        self,
    ):
        """Creating a LotusUser with Consumer role should create Django User with is_staff=False and is_superuser=False."""
        lotus_user = LotusUser.objects.create(
            email="consumer@test.com",
            role="Consumer",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="consumer@test.com")
        assert django_user.email == "consumer@test.com"
        assert django_user.is_staff is False
        assert django_user.is_superuser is False

    def test_create_lotus_user_with_custom_role_creates_django_user_without_admin_privileges(
        self,
    ):
        """Creating a LotusUser with a custom role should create Django User without admin privileges."""
        lotus_user = LotusUser.objects.create(
            email="custom@test.com",
            role="CustomRole",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="custom@test.com")
        assert django_user.email == "custom@test.com"
        assert django_user.is_staff is False
        assert django_user.is_superuser is False

    @override_settings(ADMIN_ROLE_NAME="SuperAdmin")
    def test_create_lotus_user_with_custom_admin_role_name(self):
        """Creating a LotusUser with custom ADMIN_ROLE_NAME should grant admin privileges."""
        lotus_user = LotusUser.objects.create(
            email="superadmin@test.com",
            role="SuperAdmin",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="superadmin@test.com")
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

    def test_update_lotus_user_email_updates_django_user_email(self):
        """Updating a LotusUser email should update the Django User email."""
        lotus_user = LotusUser.objects.create(
            email="original@test.com",
            role="Consumer",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="original@test.com")
        assert django_user.email == "original@test.com"

        # Update email
        lotus_user.email = "updated@test.com"
        lotus_user.save()

        # Django User username stays the same (it's the old email)
        # but email should be updated
        django_user.refresh_from_db()
        assert django_user.username == "original@test.com"  # Username doesn't change
        assert django_user.email == "updated@test.com"  # Email is updated

    def test_update_lotus_user_role_from_consumer_to_admin_grants_admin_privileges(
        self,
    ):
        """Updating a LotusUser role from Consumer to Admin should grant admin privileges."""
        lotus_user = LotusUser.objects.create(
            email="user@test.com",
            role="Consumer",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="user@test.com")
        assert django_user.is_staff is False
        assert django_user.is_superuser is False

        # Update role to Admin
        lotus_user.role = "Admin"
        lotus_user.save()

        django_user.refresh_from_db()
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

    def test_update_lotus_user_role_from_admin_to_consumer_removes_admin_privileges(
        self,
    ):
        """Updating a LotusUser role from Admin to Consumer should remove admin privileges."""
        lotus_user = LotusUser.objects.create(
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="admin@test.com")
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

        # Update role to Consumer
        lotus_user.role = "Consumer"
        lotus_user.save()

        django_user.refresh_from_db()
        assert django_user.is_staff is False
        assert django_user.is_superuser is False

    def test_update_lotus_user_other_fields_does_not_affect_django_user(self):
        """Updating other LotusUser fields should not affect Django User."""
        lotus_user = LotusUser.objects.create(
            email="user@test.com",
            role="Consumer",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="user@test.com")
        original_email = django_user.email
        original_is_staff = django_user.is_staff
        original_is_superuser = django_user.is_superuser

        # Update timezone (should not affect Django User)
        lotus_user.timezone = "America/New_York"
        lotus_user.save()

        django_user.refresh_from_db()
        assert django_user.email == original_email
        assert django_user.is_staff == original_is_staff
        assert django_user.is_superuser == original_is_superuser

    def test_create_lotus_user_when_django_user_already_exists_updates_it(self):
        """If Django User already exists, signal should update it instead of creating new one."""
        # Create Django User first
        existing_django_user = DjangoUser.objects.create_user(
            username="existing@test.com",
            email="existing@test.com",
        )
        existing_django_user.is_staff = False
        existing_django_user.is_superuser = False
        existing_django_user.save()

        # Create LotusUser with same email
        lotus_user = LotusUser.objects.create(
            email="existing@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Should update existing Django User, not create new one
        django_user_count = DjangoUser.objects.filter(
            username="existing@test.com"
        ).count()
        assert django_user_count == 1

        existing_django_user.refresh_from_db()
        assert existing_django_user.email == "existing@test.com"
        assert existing_django_user.is_staff is True
        assert existing_django_user.is_superuser is True


@pytest.mark.django_db
class TestDeleteDjangoUserSignal:
    """Tests for delete_django_user signal (post_delete)."""

    def test_delete_lotus_user_deletes_django_user(self):
        """Deleting a LotusUser should delete the corresponding Django User."""
        lotus_user = LotusUser.objects.create(
            email="delete@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Verify Django User exists
        django_user = DjangoUser.objects.get(username="delete@test.com")
        assert django_user is not None

        # Delete LotusUser
        lotus_user.delete()

        # Django User should be deleted
        assert not DjangoUser.objects.filter(username="delete@test.com").exists()

    def test_delete_lotus_user_when_django_user_does_not_exist_does_not_raise_error(
        self,
    ):
        """Deleting a LotusUser when Django User doesn't exist should not raise an error."""
        lotus_user = LotusUser.objects.create(
            email="no_django_user@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Manually delete Django User before deleting LotusUser
        DjangoUser.objects.filter(username="no_django_user@test.com").delete()

        # Deleting LotusUser should not raise an error
        lotus_user.delete()

        # Verify LotusUser is deleted
        assert not LotusUser.objects.filter(email="no_django_user@test.com").exists()

    def test_delete_lotus_user_with_admin_role_deletes_django_user(self):
        """Deleting a LotusUser with Admin role should delete the Django User."""
        lotus_user = LotusUser.objects.create(
            email="admin_delete@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Verify Django User exists with admin privileges
        django_user = DjangoUser.objects.get(username="admin_delete@test.com")
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

        # Delete LotusUser
        lotus_user.delete()

        # Django User should be deleted
        assert not DjangoUser.objects.filter(username="admin_delete@test.com").exists()
