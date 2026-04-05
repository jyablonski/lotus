"""Pytest configuration and shared fixtures for Dagster tests."""

from unittest.mock import MagicMock

from dagster import build_op_context
from dagster_dbt import DbtCliResource
import pytest

from dagster_project.resources import PostgresResource
from dagster_project.resources.example_api import ApiClientResource

try:
    from testcontainers.postgres import PostgresContainer
except ModuleNotFoundError:
    PostgresContainer = None


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


@pytest.fixture(scope="session")
def postgres_container():
    """Spin up an isolated Postgres container for Dagster integration tests."""
    if PostgresContainer is None:
        pytest.skip(
            "Skipping Postgres integration tests: testcontainers is not installed"
        )

    try:
        with PostgresContainer(
            "postgres:16-alpine",
            username="postgres",
            password="postgres",
            dbname="postgres",
        ) as postgres:
            yield postgres
    except Exception as exc:
        pytest.skip(
            f"Skipping Postgres integration tests: testcontainer unavailable ({exc})"
        )


@pytest.fixture
def postgres_resource(postgres_container):
    """Create a PostgresResource backed by a testcontainer-managed Postgres instance."""
    return PostgresResource(
        host=postgres_container.get_container_host_ip(),
        port=int(postgres_container.get_exposed_port(5432)),
        user=postgres_container.username,
        password=postgres_container.password,
        database=postgres_container.dbname,
        schema_="test",
    )


@pytest.fixture
def postgres_resource_with_cleanup(postgres_resource):
    """Ensure the isolated test schema exists before an integration test runs."""
    with postgres_resource.get_connection() as conn, conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS test")
        conn.commit()

    return postgres_resource
