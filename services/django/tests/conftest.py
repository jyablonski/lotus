import os

import pytest
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lotus_admin.settings")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(django_db_createdb, django_db_blocker):
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS source")
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            cursor.execute("SET search_path TO source, public")
            cursor.execute("DROP TABLE IF EXISTS source.users CASCADE")
            cursor.execute("""
                CREATE TABLE source.users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    email VARCHAR NOT NULL UNIQUE,
                    password VARCHAR,
                    salt VARCHAR,
                    oauth_provider VARCHAR,
                    role VARCHAR DEFAULT 'Consumer' NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                    modified_at TIMESTAMP DEFAULT NOW() NOT NULL,
                    timezone VARCHAR DEFAULT 'UTC' NOT NULL
                )
            """)
            # TODO: fix this to change core migrations to managed=True soon
            # and you can remove this fixture
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
