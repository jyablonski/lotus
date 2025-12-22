import os

import pytest
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lotus_admin.settings")


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS source")
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            connection.commit()


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
