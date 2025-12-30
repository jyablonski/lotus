"""
Tests for Django management commands.
"""

from io import StringIO

from core.models import User as LotusUser
from django.contrib.auth.models import User as DjangoUser
from django.core.management import call_command
import pytest


@pytest.mark.django_db
class TestCreateAdminUserCommand:
    """Tests for create_admin_user management command."""

    def test_create_admin_user_success(self):
        """Creating admin user when LotusUser exists with Admin role should succeed."""
        # Create LotusUser with Admin role
        LotusUser.objects.create(
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Run command
        out = StringIO()
        call_command("create_admin_user", email="admin@test.com", password="testpass123", stdout=out)

        # Verify Django User was created
        django_user = DjangoUser.objects.get(username="admin@test.com")
        assert django_user.email == "admin@test.com"
        assert django_user.is_staff is True
        assert django_user.is_superuser is True
        assert django_user.check_password("testpass123")

        # Verify output
        output = out.getvalue()
        assert "Successfully created/updated admin user" in output
        assert "admin@test.com" in output

    def test_create_admin_user_updates_existing_django_user(self):
        """Updating existing Django User should work."""
        # Create LotusUser with Admin role
        LotusUser.objects.create(
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Create Django User first
        existing_user = DjangoUser.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
        )
        existing_user.set_password("oldpassword")
        existing_user.save()

        # Run command
        out = StringIO()
        call_command("create_admin_user", email="admin@test.com", password="newpass123", stdout=out)

        # Verify Django User was updated
        django_user = DjangoUser.objects.get(username="admin@test.com")
        assert django_user.check_password("newpass123")
        assert django_user.email == "admin@test.com"

        # Verify output mentions update
        output = out.getvalue()
        assert "Updated existing Django user" in output or "Successfully created/updated" in output

    def test_create_admin_user_fails_when_lotus_user_does_not_exist(self):
        """Command should fail when LotusUser doesn't exist."""
        out = StringIO()

        call_command(
            "create_admin_user",
            email="nonexistent@test.com",
            password="testpass123",
            stdout=out,
        )

        # Verify Django User was not created
        assert not DjangoUser.objects.filter(username="nonexistent@test.com").exists()

        # Verify error message
        output = out.getvalue()
        assert "does not exist in the users table" in output

    def test_create_admin_user_fails_when_lotus_user_not_admin(self):
        """Command should fail when LotusUser exists but doesn't have Admin role."""
        # Create LotusUser with Consumer role
        LotusUser.objects.create(
            email="consumer@test.com",
            role="Consumer",
            timezone="UTC",
        )

        out = StringIO()

        call_command(
            "create_admin_user",
            email="consumer@test.com",
            password="testpass123",
            stdout=out,
        )

        # Verify Django User was not created
        assert not DjangoUser.objects.filter(username="consumer@test.com").exists()

        # Verify error message
        output = out.getvalue()
        assert "does not have Admin role" in output
        assert "Consumer" in output


@pytest.mark.django_db
class TestSyncDjangoUsersCommand:
    """Tests for sync_django_users management command."""

    def test_sync_django_users_creates_new_users(self):
        """Command should create Django Users for Lotus Users that don't have Django Users."""
        # Create LotusUsers
        LotusUser.objects.create(email="user1@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(email="admin1@test.com", role="Admin", timezone="UTC")

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        # Verify Django Users were created
        user1 = DjangoUser.objects.get(username="user1@test.com")
        assert user1.email == "user1@test.com"
        assert user1.is_staff is False
        assert user1.is_superuser is False

        admin1 = DjangoUser.objects.get(username="admin1@test.com")
        assert admin1.email == "admin1@test.com"
        assert admin1.is_staff is True
        assert admin1.is_superuser is True

        # Verify output
        output = out.getvalue()
        assert "Found 2 Lotus Users to sync" in output
        assert "Created Django User for user1@test.com" in output
        assert "Created Django User for admin1@test.com" in output
        assert "2 created" in output

    def test_sync_django_users_updates_existing_users(self):
        """Command should update Django Users when LotusUser changes."""
        # Create LotusUser
        lotus_user = LotusUser.objects.create(
            email="user@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Create Django User with wrong permissions
        django_user = DjangoUser.objects.create(
            username="user@test.com",
            email="user@test.com",
            is_staff=True,
            is_superuser=True,
        )

        # Update LotusUser role to Admin
        lotus_user.role = "Admin"
        lotus_user.save()

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        # Verify Django User was updated
        django_user.refresh_from_db()
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

        # Verify output
        output = out.getvalue()
        assert "Updated Django User for user@test.com" in output
        assert "1 updated" in output

    def test_sync_django_users_updates_email(self):
        """Command should update Django User email when LotusUser email changes."""
        # Create LotusUser
        lotus_user = LotusUser.objects.create(
            email="original@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Create Django User
        django_user = DjangoUser.objects.create(
            username="original@test.com",
            email="original@test.com",
        )

        # Update LotusUser email
        lotus_user.email = "updated@test.com"
        lotus_user.save()

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        # Verify Django User email was updated
        django_user.refresh_from_db()
        assert django_user.email == "updated@test.com"
        # Username should stay as original email
        assert django_user.username == "original@test.com"

        # Verify output
        output = out.getvalue()
        assert "Updated Django User for updated@test.com" in output

    def test_sync_django_users_skips_already_synced_users(self):
        """Command should skip users that are already in sync."""
        # Create LotusUser
        lotus_user = LotusUser.objects.create(
            email="synced@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Create Django User that's already in sync
        DjangoUser.objects.create(
            username="synced@test.com",
            email="synced@test.com",
            is_staff=False,
            is_superuser=False,
        )

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        # Verify output shows skipped
        output = out.getvalue()
        assert "Skipped synced@test.com (already in sync)" in output
        assert "1 skipped" in output

    def test_sync_django_users_dry_run(self):
        """Dry run should show what would be done without making changes."""
        # Create LotusUser
        LotusUser.objects.create(
            email="dryrun@test.com",
            role="Admin",
            timezone="UTC",
        )

        out = StringIO()
        call_command("sync_django_users", "--dry-run", stdout=out)

        # Verify Django User was NOT created
        assert not DjangoUser.objects.filter(username="dryrun@test.com").exists()

        # Verify output shows dry run
        output = out.getvalue()
        assert "DRY RUN - No changes made" in output
        assert "Created Django User for dryrun@test.com" in output

    def test_sync_django_users_mixed_scenarios(self):
        """Command should handle mix of creates, updates, and skips."""
        # Create LotusUsers
        LotusUser.objects.create(email="new@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(email="update@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(email="skip@test.com", role="Consumer", timezone="UTC")

        # Create Django User that needs updating
        django_user = DjangoUser.objects.create(
            username="update@test.com",
            email="update@test.com",
            is_staff=True,  # Wrong - should be False
            is_superuser=True,  # Wrong - should be False
        )

        # Create Django User that's already in sync
        DjangoUser.objects.create(
            username="skip@test.com",
            email="skip@test.com",
            is_staff=False,
            is_superuser=False,
        )

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        # Verify results
        assert DjangoUser.objects.filter(username="new@test.com").exists()

        django_user.refresh_from_db()
        assert django_user.is_staff is False
        assert django_user.is_superuser is False

        # Verify summary
        output = out.getvalue()
        assert "1 created" in output
        assert "1 updated" in output
        assert "1 skipped" in output
