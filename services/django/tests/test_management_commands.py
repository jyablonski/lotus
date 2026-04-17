"""
Tests for Django management commands.
"""

from io import StringIO

from core.management.commands import (
    generate_example_journal_data as generate_example_journal_data_command,
)
from core.models import (
    Journal,
    User as LotusUser,
)
from django.contrib.auth.models import (
    Group,
    User as DjangoUser,
)
from django.core.management import call_command
from django.core.management.base import CommandError
import pytest


@pytest.mark.django_db
class TestCreateAdminUserCommand:
    """Tests for create_admin_user management command."""

    def test_create_admin_user_success(self):
        """Creating admin user when LotusUser exists with Admin role should succeed."""
        # Unique email avoids collision with the conftest admin_user fixture.
        email = "cmd_admin@test.com"

        LotusUser.objects.create(
            email=email,
            role="Admin",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username=email)
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

        out = StringIO()
        call_command(
            "create_admin_user",
            email=email,
            password="testpass123",
            stdout=out,
        )

        django_user.refresh_from_db()
        assert django_user.check_password("testpass123")
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

        output = out.getvalue()
        assert "Successfully created/updated admin user" in output
        assert email in output

    def test_create_admin_user_updates_existing_django_user(self):
        """Updating existing Django User should work."""
        email = "cmd_update@test.com"

        LotusUser.objects.create(
            email=email,
            role="Admin",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username=email)
        django_user.set_password("oldpassword")
        django_user.save()

        out = StringIO()
        call_command(
            "create_admin_user",
            email=email,
            password="newpass123",
            stdout=out,
        )

        django_user.refresh_from_db()
        assert django_user.check_password("newpass123")
        assert django_user.email == email

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

        assert not DjangoUser.objects.filter(username="nonexistent@test.com").exists()

        output = out.getvalue()
        assert "does not exist in the users table" in output

    def test_create_admin_user_fails_when_lotus_user_not_admin(self):
        """Command should fail when LotusUser exists but doesn't have Admin role."""
        LotusUser.objects.create(
            email="consumer@test.com",
            role="Consumer",
            timezone="UTC",
        )

        # Delete the Django User auto-created by the signal so we can verify the
        # command does not recreate it when the Lotus user is not an Admin.
        DjangoUser.objects.filter(username="consumer@test.com").delete()

        out = StringIO()

        call_command(
            "create_admin_user",
            email="consumer@test.com",
            password="testpass123",
            stdout=out,
        )

        assert not DjangoUser.objects.filter(username="consumer@test.com").exists()

        output = out.getvalue()
        assert "does not have Admin role" in output
        assert "Consumer" in output


@pytest.mark.django_db
class TestSyncDjangoUsersCommand:
    """Tests for sync_django_users management command."""

    def test_sync_django_users_creates_new_users(self):
        """Command should create Django Users for Lotus Users that don't have Django Users."""
        LotusUser.objects.create(email="sync_user1@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(email="sync_admin1@test.com", role="Admin", timezone="UTC")

        # Remove the auto-created Django Users so the sync command has work to do.
        DjangoUser.objects.filter(
            username__in=["sync_user1@test.com", "sync_admin1@test.com"]
        ).delete()

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        user1 = DjangoUser.objects.get(username="sync_user1@test.com")
        assert user1.email == "sync_user1@test.com"
        assert user1.is_staff is False
        assert user1.is_superuser is False

        admin1 = DjangoUser.objects.get(username="sync_admin1@test.com")
        assert admin1.email == "sync_admin1@test.com"
        assert admin1.is_staff is True
        assert admin1.is_superuser is True

        output = out.getvalue()
        assert "Created Django User for sync_user1@test.com" in output
        assert "Created Django User for sync_admin1@test.com" in output
        assert "created" in output.lower()

    def test_sync_django_users_updates_existing_users(self):
        """Command should update Django Users when LotusUser changes."""
        lotus_user = LotusUser.objects.create(
            email="user@test.com",
            role="Consumer",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="user@test.com")
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.save()

        lotus_user.role = "Admin"
        lotus_user.save()

        # Reset permissions so the sync command has an update to apply.
        django_user.is_staff = False
        django_user.is_superuser = False
        django_user.save()

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        django_user.refresh_from_db()
        assert django_user.is_staff is True
        assert django_user.is_superuser is True

        output = out.getvalue()
        assert "Updated Django User for user@test.com" in output
        assert "1 updated" in output

    def test_sync_django_users_updates_email(self):
        """Command should update Django User email when LotusUser email changes."""
        # The sync command looks up Django Users by username=lotus_user.email. When a
        # LotusUser email changes, the signal updates Django User.email but not the
        # username, so the sync command can no longer locate that row. This test
        # pins down that behavior: the email change is persisted by the signal and
        # sync_django_users leaves the existing record untouched rather than
        # attempting (and failing) to recreate it.
        lotus_user = LotusUser.objects.create(
            email="original@test.com",
            role="Consumer",
            timezone="UTC",
        )

        django_user = DjangoUser.objects.get(username="original@test.com")
        lotus_user.email = "updated@test.com"
        lotus_user.save()

        django_user.refresh_from_db()
        assert django_user.email == "updated@test.com"
        assert django_user.username == "original@test.com"

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        django_user.refresh_from_db()
        assert django_user.email == "updated@test.com"
        assert django_user.username == "original@test.com"

    def test_sync_django_users_skips_already_synced_users(self):
        """Command should skip users that are already in sync."""
        LotusUser.objects.create(
            email="sync_skipped@test.com",
            role="Consumer",
            timezone="UTC",
        )

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        output = out.getvalue()
        assert "Skipped sync_skipped@test.com (already in sync)" in output
        assert "skipped" in output.lower()

    def test_sync_django_users_dry_run(self):
        """Dry run should show what would be done without making changes."""
        LotusUser.objects.create(
            email="dryrun@test.com",
            role="Admin",
            timezone="UTC",
        )

        DjangoUser.objects.filter(username="dryrun@test.com").delete()

        out = StringIO()
        call_command("sync_django_users", "--dry-run", stdout=out)

        assert not DjangoUser.objects.filter(username="dryrun@test.com").exists()

        output = out.getvalue()
        assert "DRY RUN - No changes made" in output
        assert "Created Django User for dryrun@test.com" in output

    def test_sync_django_users_mixed_scenarios(self):
        """Command should handle mix of creates, updates, and skips."""
        LotusUser.objects.create(email="sync_new@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(email="sync_update@test.com", role="Consumer", timezone="UTC")
        LotusUser.objects.create(email="sync_skip@test.com", role="Consumer", timezone="UTC")

        DjangoUser.objects.filter(username="sync_new@test.com").delete()

        # Put this user out of sync so the command must update it.
        django_user = DjangoUser.objects.get(username="sync_update@test.com")
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.save()

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        assert DjangoUser.objects.filter(username="sync_new@test.com").exists()

        django_user.refresh_from_db()
        assert django_user.is_staff is False
        assert django_user.is_superuser is False

        output = out.getvalue()
        assert "created" in output.lower()
        assert "updated" in output.lower()
        assert "skipped" in output.lower()
        assert "sync_new@test.com" in output
        assert "sync_update@test.com" in output
        assert "sync_skip@test.com" in output

    def test_sync_django_users_preserves_staff_for_allowed_group_user(self):
        """Allowed stakeholder groups should keep Django staff access after sync."""
        lotus_user = LotusUser.objects.create(
            email="stakeholder@test.com",
            role="Consumer",
            timezone="UTC",
        )
        django_user = DjangoUser.objects.get(username="stakeholder@test.com")
        product_group, _ = Group.objects.get_or_create(name="product")
        django_user.groups.add(product_group)

        django_user.refresh_from_db()
        assert django_user.is_staff is True
        assert django_user.is_superuser is False

        out = StringIO()
        call_command("sync_django_users", stdout=out)

        django_user.refresh_from_db()
        assert django_user.is_staff is True
        assert django_user.is_superuser is False

        output = out.getvalue()
        assert f"Skipped {lotus_user.email} (already in sync)" in output


@pytest.mark.django_db
class TestGenerateExampleJournalDataCommand:
    """Tests for generate_example_journal_data management command."""

    @staticmethod
    def _mock_backend_create(monkeypatch):
        backend_calls = []

        def fake_create(
            self,
            *,
            session,
            backend_base_url,
            backend_api_key,
            user_id,
            journal_text,
            mood_score,
            timeout,
            max_retries,
        ):
            journal = Journal.objects.create(
                user_id=user_id,
                journal_text=journal_text,
                mood_score=mood_score,
            )
            backend_calls.append(
                {
                    "backend_base_url": backend_base_url,
                    "backend_api_key": backend_api_key,
                    "user_id": user_id,
                    "journal_text": journal_text,
                    "mood_score": mood_score,
                    "timeout": timeout,
                    "max_retries": max_retries,
                    "journal_id": journal.id,
                }
            )
            return journal.id

        monkeypatch.setattr(
            generate_example_journal_data_command.Command,
            "_create_journal_via_backend",
            fake_create,
        )
        return backend_calls

    def test_generate_example_journal_data_creates_users_and_journals(self, monkeypatch):
        prefix = "cmd-seed"
        out = StringIO()
        backend_calls = self._mock_backend_create(monkeypatch)

        call_command(
            "generate_example_journal_data",
            "--users",
            "3",
            "--journals",
            "12",
            "--seed",
            "7",
            "--email-prefix",
            prefix,
            "--backend-base-url",
            "http://backend.test:8080",
            "--backend-api-key",
            "test-backend-key",
            stdout=out,
        )

        generated_users = LotusUser.objects.filter(email__startswith=f"{prefix}-").order_by("email")
        generated_journals = Journal.objects.filter(user__email__startswith=f"{prefix}-")
        django_users = DjangoUser.objects.filter(username__startswith=f"{prefix}-")

        assert generated_users.count() == 3
        assert generated_journals.count() == 12
        assert django_users.count() == 3
        assert len(backend_calls) == 12
        assert all(call["backend_base_url"] == "http://backend.test:8080" for call in backend_calls)
        assert all(call["backend_api_key"] == "test-backend-key" for call in backend_calls)
        assert all(call["max_retries"] == 6 for call in backend_calls)
        assert all(journal.mood_score is not None for journal in generated_journals)
        assert all(1 <= journal.mood_score <= 10 for journal in generated_journals)
        assert generated_journals.first().journal_text.startswith("Entry ")

        output = out.getvalue()
        assert "Generated 3 users and 12 journals" in output
        assert "Created 12/12 journals via backend" in output
        assert f"{prefix}-" in output

    def test_generate_example_journal_data_reset_prefix_replaces_existing_data(self, monkeypatch):
        prefix = "cmd-reset"
        self._mock_backend_create(monkeypatch)

        call_command(
            "generate_example_journal_data",
            "--users",
            "2",
            "--journals",
            "5",
            "--seed",
            "10",
            "--email-prefix",
            prefix,
            "--backend-api-key",
            "test-backend-key",
        )

        call_command(
            "generate_example_journal_data",
            "--users",
            "1",
            "--journals",
            "2",
            "--seed",
            "10",
            "--email-prefix",
            prefix,
            "--reset-prefix",
            "--backend-api-key",
            "test-backend-key",
        )

        assert LotusUser.objects.filter(email__startswith=f"{prefix}-").count() == 1
        assert DjangoUser.objects.filter(username__startswith=f"{prefix}-").count() == 1
        assert Journal.objects.filter(user__email__startswith=f"{prefix}-").count() == 2

    def test_generate_example_journal_data_surfaces_backend_errors(self, monkeypatch):
        def fake_create(
            self,
            *,
            session,
            backend_base_url,
            backend_api_key,
            user_id,
            journal_text,
            mood_score,
            timeout,
            max_retries,
        ):
            raise CommandError("backend journal creation failed with status 503")

        monkeypatch.setattr(
            generate_example_journal_data_command.Command,
            "_create_journal_via_backend",
            fake_create,
        )

        with pytest.raises(CommandError, match="status 503"):
            call_command(
                "generate_example_journal_data",
                "--users",
                "1",
                "--journals",
                "1",
                "--email-prefix",
                "cmd-backend-fail",
                "--backend-api-key",
                "test-backend-key",
            )

        assert Journal.objects.filter(user__email__startswith="cmd-backend-fail-").count() == 0

    def test_generate_example_journal_data_requires_backend_api_key(self):
        with pytest.raises(CommandError, match="BACKEND_API_KEY must be set"):
            call_command(
                "generate_example_journal_data",
                "--users",
                "1",
                "--journals",
                "1",
                "--email-prefix",
                "cmd-no-backend-key",
                "--backend-api-key",
                "",
            )

    def test_generate_example_journal_data_rejects_invalid_counts(self):
        with pytest.raises(CommandError, match="--users must be greater than 0"):
            call_command("generate_example_journal_data", "--users", "0")

    def test_generate_example_journal_data_rejects_invalid_request_rate(self):
        with pytest.raises(CommandError, match="--requests-per-second must be greater than 0"):
            call_command("generate_example_journal_data", "--requests-per-second", "0")
