import os

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lotus_admin.settings")


@pytest.fixture
def admin_user(db):
    from core.models import User as LotusUser
    from django.contrib.auth.models import User as DjangoUser

    admin_email = "admin@test.com"

    # Create Django User for authentication
    django_user, created = DjangoUser.objects.get_or_create(
        username="admin",
        defaults={
            "email": admin_email,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        django_user.set_password("testpass123")
        django_user.save()
    else:
        # Ensure existing user has proper permissions and email for tests
        django_user.email = admin_email
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.save()

    # Create matching LotusUser with Admin role (required by middleware)
    LotusUser.objects.get_or_create(
        email=admin_email,
        defaults={"role": "Admin", "timezone": "UTC"},
    )

    return django_user


@pytest.fixture
def admin_client(admin_user, client):
    client.force_login(admin_user)
    return client
