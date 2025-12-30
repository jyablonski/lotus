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
        # Create LotusUser with Admin role (signal will create Django User)
        LotusUser.objects.create(
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Delete Django User created by signal to test command creation
        DjangoUser.objects.filter(username="admin@test.com").delete()

        # Run command
        out = StringIO()
        call_command(
            "create_admin_user",
            email="admin@test.com",
            password="testpass123",
            stdout=out,
        )

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
        # Create LotusUser with Admin role (signal will create Django User)
        LotusUser.objects.create(
            email="admin@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Get Django User created by signal and set password
        django_user = DjangoUser.objects.get(username="admin@test.com")
        django_user.set_password("oldpassword")
        django_user.save()

        # Run command
        out = StringIO()
        call_command(
            "create_admin_user",
            email="admin@test.com",
            password="newpass123",
            stdout=out,
        )

        # Verify Django User was updated
        django_user.refresh_from_db()
        assert django_user.check_password("newpass123")
        assert django_user.email == "admin@test.com"

        # Verify output mentions update
        output = out.getvalue()
        assert (
            "Updated existing Django user" in output
            or "Successfully created/updated" in output
        )

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
        # Create LotusUser with Consumer role (signal will create Django User)
        LotusUser.objects.create(
            email="consumer@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Delete Django User created by signal - command should not recreate it
        DjangoUser.objects.filter(username="consumer@test.com").delete()

        out = StringIO()

        call_command(
            "create_admin_user",
            email="consumer@test.com",
            password="testpass123",
            stdout=out,
        )

        # Verify Django User was not created by command (signal would create it, but we deleted it)
        # The command should fail before creating a user
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
        # Create LotusUsers (signals will create Django Users)
        LotusUser.objects.create(
            email="user1@test.com", role="Consumer", timezone="UTC"
        )
        LotusUser.objects.create(email="admin1@test.com", role="Admin", timezone="UTC")

        # Delete Django Users created by signals to test command creation
        DjangoUser.objects.filter(username__in=["user1@test.com", "admin1@test.com"]).delete()

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
        # Create LotusUser (signal will create Django User)
        lotus_user = LotusUser.objects.create(
            email="user@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Get Django User created by signal and set wrong permissions
        django_user = DjangoUser.objects.get(username="user@test.com")
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.save()

        # Update LotusUser role to Admin (signal will update Django User, but we test command too)
        lotus_user.role = "Admin"
        lotus_user.save()

        # Reset permissions to test command update
        django_user.is_staff = False
        django_user.is_superuser = False
        django_user.save()

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
        # Create LotusUser (signal will create Django User)
        lotus_user = LotusUser.objects.create(
            email="original@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Get Django User created by signal
        django_user = DjangoUser.objects.get(username="original@test.com")

        # Update LotusUser email (signal will update Django User email)
        lotus_user.email = "updated@test.com"
        lotus_user.save()

        # Reset email to test command update
        django_user.email = "original@test.com"
        django_user.save()

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
        # Create LotusUser (signal will create Django User that's already in sync)
        LotusUser.objects.create(
            email="synced@test.com",
            role="Consumer",
            timezone="UTC",
        )

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        # Verify output shows skipped
        output = out.getvalue()
        assert "Skipped synced@test.com (already in sync)" in output
        assert "1 skipped" in output

    def test_sync_django_users_dry_run(self):
        """Dry run should show what would be done without making changes."""
        # Create LotusUser (signal will create Django User)
        LotusUser.objects.create(
            email="dryrun@test.com",
            role="Admin",
            timezone="UTC",
        )

        # Delete Django User created by signal - dry run should show it would be created
        DjangoUser.objects.filter(username="dryrun@test.com").delete()

        out = StringIO()
        call_command("sync_django_users", "--dry-run", stdout=out)

        # Verify Django User was NOT created by command (signal would create it, but we deleted it)
        assert not DjangoUser.objects.filter(username="dryrun@test.com").exists()

        # Verify output shows dry run
        output = out.getvalue()
        assert "DRY RUN - No changes made" in output
        assert "Created Django User for dryrun@test.com" in output

    def test_sync_django_users_mixed_scenarios(self):
        """Command should handle mix of creates, updates, and skips."""
        # Create LotusUsers (signals will create Django Users)
        LotusUser.objects.create(email="new@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(
            email="update@test.com", role="Consumer", timezone="UTC"
        )
        LotusUser.objects.create(email="skip@test.com", role="Consumer", timezone="UTC")

        # Delete Django User for "new" to test creation
        DjangoUser.objects.filter(username="new@test.com").delete()

        # Get Django User that needs updating and set wrong permissions
        django_user = DjangoUser.objects.get(username="update@test.com")
        django_user.is_staff = True  # Wrong - should be False
        django_user.is_superuser = True  # Wrong - should be False
        django_user.save()

        # Django User for "skip" is already in sync (created by signal)

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
