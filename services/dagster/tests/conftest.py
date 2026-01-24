"""Pytest configuration and shared fixtures for Dagster tests."""

import os
from unittest.mock import MagicMock

from dagster import build_op_context, EnvVar
from dagster_dbt import DbtCliResource
import pytest

from dagster_project.resources import PostgresResource
from dagster_project.resources.example_api import ApiClientResource


@pytest.fixture
def mock_api_client_resource():
    """Mock ApiClientResource for unit tests."""
    mock_resource = MagicMock(spec=ApiClientResource)
    mock_session = MagicMock()
    mock_resource.get_client.return_value = mock_session
    return mock_resource


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
    # Use EnvVar() for environment variable lookup - Dagster will evaluate these at runtime
    # Set test-specific defaults as env vars if not already set, so EnvVar() can use them
    # This maintains backward compatibility while using EnvVar() for deferred evaluation
    test_defaults = {
        "TEST_POSTGRES_HOST": "localhost",
        "TEST_POSTGRES_PORT": "5432",
        "TEST_POSTGRES_USER": "postgres",
        "TEST_POSTGRES_PASSWORD": "postgres",
        "TEST_POSTGRES_DB": "postgres",
        "TEST_POSTGRES_SCHEMA": "test",
    }
    for key, default_value in test_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value

    return PostgresResource(
        host=EnvVar("TEST_POSTGRES_HOST"),
        port=EnvVar.int("TEST_POSTGRES_PORT"),
        user=EnvVar("TEST_POSTGRES_USER"),
        password=EnvVar("TEST_POSTGRES_PASSWORD"),
        database=EnvVar("TEST_POSTGRES_DB"),
        schema_=EnvVar("TEST_POSTGRES_SCHEMA"),
    )


@pytest.fixture
def postgres_resource_with_cleanup(postgres_resource):
    """PostgresResource fixture that ensures test schema exists.

    Creates the test schema if it doesn't exist. No cleanup is performed.
    """
    # Ensure test schema exists
    schema_name = postgres_resource.schema_
    with postgres_resource.get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        conn.commit()

    return postgres_resource
