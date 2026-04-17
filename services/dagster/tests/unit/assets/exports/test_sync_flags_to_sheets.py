"""Unit tests for sync_flags_to_sheets assets."""

from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import polars as pl
import pytest

from dagster_project.assets.exports.sync_flags_to_sheets import (
    get_feature_flags_from_postgres,
    sync_flags_to_sheets,
)


def _make_mock_postgres(df: pl.DataFrame) -> MagicMock:
    """Create a mock PostgresResource whose query_to_polars returns *df*."""
    mock = MagicMock()
    mock.query_to_polars.return_value = df
    return mock


def _build_context_with_sheet(sheet_resource: MagicMock):
    def _fn(_context):
        return sheet_resource

    context = build_op_context(
        resources={"feature_flags_google_sheet": ResourceDefinition(resource_fn=_fn)}
    )
    context.log.info = MagicMock()
    context.log.error = MagicMock()
    return context


@pytest.mark.unit
class TestGetFeatureFlagsFromPostgres:
    """Test the get_feature_flags_from_postgres asset."""

    def test_get_feature_flags_from_postgres_success(self):
        expected_df = pl.DataFrame(
            {
                "id": [1, 2, 3],
                "flag_name": [
                    "enable_feature_a",
                    "enable_feature_b",
                    "enable_feature_c",
                ],
                "enabled": [True, False, True],
                "created_at": [
                    "2024-01-01 10:00:00",
                    "2024-01-02 11:00:00",
                    "2024-01-03 12:00:00",
                ],
                "modified_at": [
                    "2024-01-01 10:00:00",
                    "2024-01-02 11:00:00",
                    "2024-01-03 12:00:00",
                ],
            }
        )
        mock_postgres = _make_mock_postgres(expected_df)

        def resource_fn(_context):
            return mock_postgres

        context = build_op_context(
            resources={"postgres_conn": ResourceDefinition(resource_fn=resource_fn)}
        )

        result = get_feature_flags_from_postgres(context)

        mock_postgres.query_to_polars.assert_called_once_with(
            "SELECT * FROM feature_flags"
        )
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_get_feature_flags_from_postgres_empty_result(self):
        expected_df = pl.DataFrame({"id": [], "flag_name": [], "enabled": []})
        mock_postgres = _make_mock_postgres(expected_df)

        def resource_fn(_context):
            return mock_postgres

        context = build_op_context(
            resources={"postgres_conn": ResourceDefinition(resource_fn=resource_fn)}
        )

        result = get_feature_flags_from_postgres(context)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0


@pytest.mark.unit
class TestSyncFlagsToSheets:
    """Test the sync_flags_to_sheets asset (delegates to overwrite_with_rows)."""

    def test_sync_flags_delegates_to_overwrite_with_rows(self):
        mock_df = pl.DataFrame(
            {
                "id": [1, 2],
                "flag_name": ["enable_feature_a", "enable_feature_b"],
                "enabled": [True, False],
            }
        )
        mock_sheet_resource = MagicMock()
        context = _build_context_with_sheet(mock_sheet_resource)

        result = sync_flags_to_sheets(context, mock_df)

        assert result is None
        mock_sheet_resource.overwrite_with_rows.assert_called_once()
        kwargs = mock_sheet_resource.overwrite_with_rows.call_args.kwargs
        assert kwargs["worksheet_name"] == "Feature Flags"
        assert kwargs["header"] == [
            "id",
            "flag_name",
            "enabled",
            "synced_at",
        ]
        assert len(kwargs["rows"]) == 2
        for row in kwargs["rows"]:
            for value in row:
                assert isinstance(value, str)

    def test_sync_flags_handles_empty_dataframe(self):
        mock_df = pl.DataFrame({"id": [], "flag_name": [], "enabled": []})
        mock_sheet_resource = MagicMock()
        context = _build_context_with_sheet(mock_sheet_resource)

        result = sync_flags_to_sheets(context, mock_df)

        assert result is None
        kwargs = mock_sheet_resource.overwrite_with_rows.call_args.kwargs
        assert kwargs["rows"] == []
        assert "synced_at" in kwargs["header"]

    def test_sync_flags_raises_and_logs_on_exception(self):
        mock_df = pl.DataFrame({"id": [1], "flag_name": ["a"], "enabled": [True]})
        mock_sheet_resource = MagicMock()
        mock_sheet_resource.overwrite_with_rows.side_effect = Exception(
            "Google API Error"
        )
        context = _build_context_with_sheet(mock_sheet_resource)

        with pytest.raises(Exception, match="Google API Error"):
            sync_flags_to_sheets(context, mock_df)

        context.log.error.assert_called_once()
        assert "Error syncing to Google Sheets" in context.log.error.call_args[0][0]
