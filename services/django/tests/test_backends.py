import pytest
from core.backends import LotusUserBackend
from core.models import User as LotusUser
from django.contrib.auth.models import User as DjangoUser


@pytest.mark.django_db
class TestLotusUserBackend:
    def test_authenticate_oauth_user(self):
        """OAuth user (no password) should authenticate and create Django user."""
        LotusUser.objects.create(
            email="oauth@example.com",
            oauth_provider="github",
            password=None,
        )

        backend = LotusUserBackend()
        user = backend.authenticate(None, username="oauth@example.com", password=None)

        assert user is not None
        assert user.username == "oauth@example.com"
        assert DjangoUser.objects.filter(username="oauth@example.com").exists()

    def test_authenticate_password_user(self):
        """Password user should authenticate and create Django user."""
        LotusUser.objects.create(
            email="password@example.com",
            password="hashed_password",
            salt="salt123",
        )

        backend = LotusUserBackend()
        user = backend.authenticate(
            None, username="password@example.com", password="somepass"
        )

        assert user is not None
        assert user.username == "password@example.com"

    def test_authenticate_user_not_found(self):
        """Non-existent user should return None."""
        backend = LotusUserBackend()
        user = backend.authenticate(None, username="nonexistent@example.com")

        assert user is None

    def test_authenticate_with_email_kwarg(self):
        """Should accept email as keyword argument."""
        LotusUser.objects.create(
            email="kwarg@example.com",
            oauth_provider="google",
        )

        backend = LotusUserBackend()
        user = backend.authenticate(None, email="kwarg@example.com")

        assert user is not None
        assert user.username == "kwarg@example.com"

    def test_get_user_exists(self):
        """get_user should return Django user if exists."""
        django_user = DjangoUser.objects.create_user(
            username="getuser@example.com",
            email="getuser@example.com",
        )

        backend = LotusUserBackend()
        user = backend.get_user(django_user.id)

        assert user is not None
        assert user.id == django_user.id

    def test_get_user_not_found(self):
        """get_user should return None if user doesn't exist."""
        backend = LotusUserBackend()
        user = backend.get_user(99999)

        assert user is None
