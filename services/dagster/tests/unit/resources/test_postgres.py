"""Tests for PostgresResource."""

from unittest.mock import MagicMock, patch

import pytest

from dagster_project.resources import PostgresResource


@pytest.mark.unit
class TestPostgresResource:
    """Test the PostgresResource."""

    def test_postgres_resource_initialization(self):
        """Test resource initialization with defaults."""
        resource = PostgresResource()
        assert resource.host == "postgres"
        assert resource.port == 5432
        assert resource.user == "postgres"
        assert resource.password == "postgres"
        assert resource.database == "postgres"
        assert resource.schema_ == "source"

    def test_postgres_resource_custom_config(self):
        """Test resource initialization with custom config."""
        resource = PostgresResource(
            host="custom_host",
            port=5433,
            user="custom_user",
            password="custom_pass",
            database="custom_db",
            schema_="custom_schema",
        )
        assert resource.host == "custom_host"
        assert resource.port == 5433
        assert resource.user == "custom_user"
        assert resource.password == "custom_pass"
        assert resource.database == "custom_db"
        assert resource.schema_ == "custom_schema"

    @patch("dagster_project.resources.postgres.psycopg2.connect")
    def test_get_connection(self, mock_connect):
        """Test connection context manager."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        resource = PostgresResource()
        with resource.get_connection() as conn:
            assert conn == mock_conn

        mock_connect.assert_called_once_with(
            host="postgres",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres",
            options="-c search_path=source",
        )
        mock_conn.close.assert_called_once()
