"""Tests for PostgresResource."""

from unittest.mock import MagicMock, patch

import polars as pl
import pytest
from psycopg2.extras import Json

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

    @patch("dagster_project.resources.postgres.execute_values")
    @patch("dagster_project.resources.postgres.psycopg2.connect")
    def test_write_to_postgres_upserts_dataframe(
        self, mock_connect, mock_execute_values
    ):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        df = pl.DataFrame(
            {
                "source_id": ["example-001", "example-002"],
                "payload": [{"status": "created"}, {"status": "updated"}],
                "modified_at": ["2026-04-17T06:01:00Z", "2026-04-17T07:15:00Z"],
            }
        )

        row_count = PostgresResource().write_to_postgres(
            df=df,
            table_name="example_api_records",
            conflict_columns=["source_id"],
            json_columns=["payload"],
        )

        assert row_count == 2
        mock_execute_values.assert_called_once()
        query = mock_execute_values.call_args.args[1]
        values = mock_execute_values.call_args.args[2]

        assert 'INSERT INTO "example_api_records"' in query
        assert '("source_id", "payload", "modified_at") VALUES %s' in query
        assert 'ON CONFLICT ("source_id") DO UPDATE SET' in query
        assert '"payload" = EXCLUDED."payload"' in query
        assert values[0][0] == "example-001"
        assert isinstance(values[0][1], Json)
        assert values[0][2] == "2026-04-17T06:01:00Z"
        mock_conn.commit.assert_called_once()

    @patch("dagster_project.resources.postgres.execute_values")
    def test_write_to_postgres_uses_existing_cursor(self, mock_execute_values):
        mock_cursor = MagicMock()
        df = pl.DataFrame({"id": [1], "name": ["Ada"]})

        row_count = PostgresResource().write_to_postgres(
            df=df,
            table_name="source.people",
            conflict_columns=["id"],
            update_columns=["name"],
            cursor=mock_cursor,
        )

        assert row_count == 1
        mock_execute_values.assert_called_once()
        query = mock_execute_values.call_args.args[1]
        assert 'INSERT INTO "source"."people"' in query
        assert 'ON CONFLICT ("id") DO UPDATE SET "name" = EXCLUDED."name"' in query

    @patch("dagster_project.resources.postgres.execute_values")
    def test_write_to_postgres_noops_on_empty_dataframe(self, mock_execute_values):
        df = pl.DataFrame(schema={"id": pl.Int64, "name": pl.String})

        row_count = PostgresResource().write_to_postgres(
            df=df,
            table_name="people",
        )

        assert row_count == 0
        mock_execute_values.assert_not_called()
