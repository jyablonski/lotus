import os

import pytest
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lotus_admin.settings")


def get_unmanaged_models():
    """Return all models with managed=False."""
    from django.apps import apps

    return [m for m in apps.get_models() if not m._meta.managed]


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
                try:
                    schema_editor.create_model(model)
                except Exception:
                    # Table might already exist from a previous test run
                    pass


@pytest.fixture
def admin_user(db):
    from django.contrib.auth.models import User

    return User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="testpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def admin_client(admin_user, client):
    client.force_login(admin_user)
    return client
