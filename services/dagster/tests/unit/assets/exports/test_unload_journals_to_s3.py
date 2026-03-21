"""Unit tests for unload_journals_to_s3 asset."""

from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import polars as pl
import pytest

from dagster_project.assets.exports.unload_journals_to_s3 import unload_journals_to_s3
from dagster_project.sql.exports import SELECT_USER_JOURNAL_SUMMARY


def _make_mock_postgres(df: pl.DataFrame) -> MagicMock:
    """Create a mock PostgresResource whose query_to_polars returns *df*."""
    mock = MagicMock()
    mock.query_to_polars.return_value = df
    return mock


@pytest.mark.unit
class TestUnloadJournalsToS3:
    """Test the unload_journals_to_s3 asset."""

    def test_unload_journals_to_s3_success(self):
        """Test successful unload of journals from Postgres."""
        expected_df = pl.DataFrame(
            {
                "id": [1, 2, 3],
                "user_name": ["user1", "user2", "user3"],
                "amount": [100.0, 200.0, 150.0],
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            }
        )
        mock_postgres = _make_mock_postgres(expected_df)

        def resource_fn(_context):
            return mock_postgres

        context = build_op_context(
            resources={"postgres_conn": ResourceDefinition(resource_fn=resource_fn)}
        )

        result = unload_journals_to_s3(context)

        mock_postgres.query_to_polars.assert_called_once_with(
            SELECT_USER_JOURNAL_SUMMARY
        )
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ["id", "user_name", "amount", "date"]

    def test_unload_journals_to_s3_empty_result(self):
        """Test handling of empty query result."""
        expected_df = pl.DataFrame(
            {
                "id": [],
                "user_name": [],
                "amount": [],
                "date": [],
            }
        )
        mock_postgres = _make_mock_postgres(expected_df)

        def resource_fn(_context):
            return mock_postgres

        context = build_op_context(
            resources={"postgres_conn": ResourceDefinition(resource_fn=resource_fn)}
        )

        result = unload_journals_to_s3(context)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0

    def test_unload_journals_to_s3_logs_info(self):
        """Test that asset logs information about the dataframe."""
        expected_df = pl.DataFrame(
            {
                "id": [1],
                "user_name": ["user1"],
                "amount": [100.0],
                "date": ["2024-01-01"],
            }
        )
        mock_postgres = _make_mock_postgres(expected_df)

        def resource_fn(_context):
            return mock_postgres

        context = build_op_context(
            resources={"postgres_conn": ResourceDefinition(resource_fn=resource_fn)}
        )
        context.log.info = MagicMock()

        result = unload_journals_to_s3(context)

        # Verify logging was called (asset logs twice: total rows and first 10 rows)
        assert context.log.info.call_count == 2
        assert isinstance(result, pl.DataFrame)
