"""Pytest configuration and shared fixtures for Dagster tests."""

import os

import pytest
from unittest.mock import MagicMock
from dagster import build_op_context
from dagster_dbt import DbtCliResource

from dagster_project.resources import PostgresResource


@pytest.fixture
def mock_postgres_resource():
    """Mock PostgresResource for unit tests."""
    mock_resource = MagicMock(spec=PostgresResource)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_resource.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_resource


@pytest.fixture
def mock_dbt_resource():
    """Mock DbtCliResource for unit tests."""
    mock_resource = MagicMock(spec=DbtCliResource)
    return mock_resource


@pytest.fixture
def asset_context():
    """Create a test asset execution context."""
    return build_op_context()


@pytest.fixture
def postgres_resource():
    """Create a real PostgresResource for integration tests.

    Assumes Docker Compose postgres service is running and available.
    Uses the same connection settings as docker-compose-local.yaml:
    - host: localhost (from host machine) or postgres (from within Docker network)
    - port: 5432
    - user: postgres
    - password: postgres
    - database: postgres
    - schema: test (for test isolation)

    To start the postgres service:
        docker-compose -f docker/docker-compose-local.yaml up -d postgres
    """
    # Allow override via env vars, but default to Docker Compose postgres settings
    return PostgresResource(
        host=os.getenv("TEST_POSTGRES_HOST", "localhost"),
        port=int(os.getenv("TEST_POSTGRES_PORT", "5432")),
        user=os.getenv("TEST_POSTGRES_USER", "postgres"),
        password=os.getenv("TEST_POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("TEST_POSTGRES_DB", "postgres"),
        schema_=os.getenv("TEST_POSTGRES_SCHEMA", "test"),
    )


@pytest.fixture
def postgres_resource_with_cleanup(postgres_resource):
    """PostgresResource fixture that ensures test schema exists and cleans up after tests.

    Creates the test schema if it doesn't exist and drops test tables after each test.
    """
    # Ensure test schema exists
    schema_name = postgres_resource.schema_
    with postgres_resource.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            conn.commit()

    yield postgres_resource

    # Cleanup: drop test tables (but keep schema)
    with postgres_resource.get_connection() as conn:
        with conn.cursor() as cur:
            # Drop all tables in test schema
            cur.execute(f"""
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '{schema_name}')
                    LOOP
                        EXECUTE 'DROP TABLE IF EXISTS {schema_name}.' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
            conn.commit()
