import contextlib
import os

from django.db import connection
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lotus_admin.settings")


def get_unmanaged_models():
    """Return all models with managed=False, sorted by dependencies."""
    from django.apps import apps

    unmanaged = [m for m in apps.get_models() if not m._meta.managed]

    # Sort models so parent tables are created before children (FKs)
    def get_dependencies(model):
        """Count number of FK dependencies to other unmanaged models."""
        count = 0
        for field in model._meta.get_fields():
            if hasattr(field, "related_model") and field.related_model in unmanaged:
                count += 1
        return count

    return sorted(unmanaged, key=get_dependencies)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(django_db_setup, django_db_blocker):
    """Create tables for unmanaged models during test setup."""
    unmanaged_models = get_unmanaged_models()

    with django_db_blocker.unblock():
        # Create schema and extensions
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS source")
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

        # Use schema editor to create tables for unmanaged models
        with connection.schema_editor() as schema_editor:
            for model in unmanaged_models:
                with contextlib.suppress(Exception):
                    schema_editor.create_model(model)  # Table might already exist


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
