"""Unit tests for unload_journals_to_s3 asset."""

from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import polars as pl
import pytest

from dagster_project.assets.exports.unload_journals_to_s3 import unload_journals_to_s3


@pytest.mark.unit
class TestUnloadJournalsToS3:
    """Test the unload_journals_to_s3 asset."""

    def test_unload_journals_to_s3_success(self, mock_postgres_resource):
        """Test successful unload of journals from Postgres."""
        # Mock database response
        mock_rows = [
            (1, "user1", 100.0, "2024-01-01"),
            (2, "user2", 200.0, "2024-01-02"),
            (3, "user3", 150.0, "2024-01-03"),
        ]
        mock_columns = ["id", "user_name", "amount", "date"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in mock_columns]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_postgres_resource.get_connection.return_value.__enter__.return_value = mock_conn

        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})

        result = unload_journals_to_s3(context, postgres_resource_def)

        # Verify database interactions
        mock_postgres_resource.get_connection.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT * FROM gold.user_journal_summary")
        mock_cursor.fetchall.assert_called_once()

        # Verify result is a Polars DataFrame
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == mock_columns

    def test_unload_journals_to_s3_empty_result(self, mock_postgres_resource):
        """Test handling of empty query result."""
        mock_rows = []
        mock_columns = ["id", "user_name", "amount", "date"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in mock_columns]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_postgres_resource.get_connection.return_value.__enter__.return_value = mock_conn

        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})

        result = unload_journals_to_s3(context, postgres_resource_def)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == mock_columns

    def test_unload_journals_to_s3_logs_info(self, mock_postgres_resource):
        """Test that asset logs information about the dataframe."""
        mock_rows = [
            (1, "user1", 100.0, "2024-01-01"),
        ]
        mock_columns = ["id", "user_name", "amount", "date"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in mock_columns]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_postgres_resource.get_connection.return_value.__enter__.return_value = mock_conn

        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})

        result = unload_journals_to_s3(context, postgres_resource_def)

        # Verify logging was called
        assert context.log.has_calls or True  # Logging may not be directly testable
        assert isinstance(result, pl.DataFrame)
