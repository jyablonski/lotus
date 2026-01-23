"""Unit tests for sync_flags_to_sheets assets."""

from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import gspread
import polars as pl
import pytest

from dagster_project.assets.exports.sync_flags_to_sheets import (
    get_feature_flags_from_postgres,
    sync_flags_to_sheets,
)


@pytest.mark.unit
class TestGetFeatureFlagsFromPostgres:
    """Test the get_feature_flags_from_postgres asset."""

    def test_get_feature_flags_from_postgres_success(self, mock_postgres_resource):
        """Test successful fetch of feature flags from Postgres."""
        # Mock database response
        mock_rows = [
            (1, "enable_feature_a", True, "2024-01-01 10:00:00", "2024-01-01 10:00:00"),
            (
                2,
                "enable_feature_b",
                False,
                "2024-01-02 11:00:00",
                "2024-01-02 11:00:00",
            ),
            (3, "enable_feature_c", True, "2024-01-03 12:00:00", "2024-01-03 12:00:00"),
        ]
        mock_columns = ["id", "flag_name", "enabled", "created_at", "modified_at"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in mock_columns]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_postgres_resource.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})

        result = get_feature_flags_from_postgres(context)

        # Verify database interactions
        mock_postgres_resource.get_connection.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT * FROM feature_flags")
        mock_cursor.fetchall.assert_called_once()

        # Verify result is a Polars DataFrame
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == mock_columns

    def test_get_feature_flags_from_postgres_empty_result(self, mock_postgres_resource):
        """Test handling of empty query result."""
        mock_rows = []
        mock_columns = ["id", "flag_name", "enabled", "created_at", "modified_at"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in mock_columns]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_postgres_resource.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})

        result = get_feature_flags_from_postgres(context)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == mock_columns

    def test_get_feature_flags_from_postgres_logs_info(self, mock_postgres_resource):
        """Test that asset logs information about the dataframe."""
        mock_rows = [
            (1, "enable_feature_a", True, "2024-01-01 10:00:00", "2024-01-01 10:00:00"),
        ]
        mock_columns = ["id", "flag_name", "enabled", "created_at", "modified_at"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [(col,) for col in mock_columns]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_postgres_resource.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})

        # Mock the log methods to verify they're called
        context.log.info = MagicMock()

        result = get_feature_flags_from_postgres(context)

        # Verify logging was called (asset logs fetched count and columns)
        assert context.log.info.call_count == 2
        assert isinstance(result, pl.DataFrame)


@pytest.mark.unit
class TestSyncFlagsToSheets:
    """Test the sync_flags_to_sheets asset."""

    def test_sync_flags_to_sheets_success(self):
        """Test successful sync of feature flags to Google Sheets."""
        # Create mock DataFrame (simulating output from get_feature_flags_from_postgres)
        mock_df = pl.DataFrame(
            {
                "id": [1, 2],
                "flag_name": ["enable_feature_a", "enable_feature_b"],
                "enabled": [True, False],
                "created_at": ["2024-01-01 10:00:00", "2024-01-02 11:00:00"],
                "modified_at": ["2024-01-01 10:00:00", "2024-01-02 11:00:00"],
            }
        )

        # Mock Google Sheets resource
        mock_google_sheets_resource = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_google_sheets_resource.get_sheet.return_value = mock_sheet

        def google_sheets_resource_fn(_context):
            return mock_google_sheets_resource

        google_sheets_resource_def = ResourceDefinition(
            resource_fn=google_sheets_resource_fn
        )
        context = build_op_context(
            resources={"feature_flags_google_sheet": google_sheets_resource_def}
        )

        # Mock log methods
        context.log.info = MagicMock()
        context.log.error = MagicMock()

        result = sync_flags_to_sheets(context, mock_df)

        # Verify Google Sheets interactions
        mock_google_sheets_resource.get_sheet.assert_called_once()
        mock_sheet.worksheet.assert_called_once_with("Feature Flags")
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once()

        # Verify update was called with correct data structure
        update_call_args = mock_worksheet.update.call_args
        assert update_call_args[0][0] == "A1"
        assert update_call_args[1]["value_input_option"] == "RAW"

        # Verify the data structure includes headers + rows
        all_rows = update_call_args[0][1]
        assert len(all_rows) == 3  # headers + 2 data rows
        assert all_rows[0] == [
            "id",
            "flag_name",
            "enabled",
            "created_at",
            "modified_at",
            "synced_at",
        ]  # headers + synced_at

        # Verify logging
        assert context.log.info.call_count == 1
        assert context.log.error.call_count == 0

        # Verify result
        assert result is None

    def test_sync_flags_to_sheets_creates_worksheet_if_not_exists(self):
        """Test that worksheet is created if it doesn't exist."""
        mock_df = pl.DataFrame(
            {
                "id": [1],
                "flag_name": ["enable_feature_a"],
                "enabled": [True],
                "created_at": ["2024-01-01 10:00:00"],
                "modified_at": ["2024-01-01 10:00:00"],
            }
        )

        mock_google_sheets_resource = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()

        # Simulate worksheet not found, then create it
        mock_sheet.worksheet.side_effect = gspread.WorksheetNotFound("Not found")
        mock_sheet.add_worksheet.return_value = mock_worksheet
        mock_google_sheets_resource.get_sheet.return_value = mock_sheet

        def google_sheets_resource_fn(_context):
            return mock_google_sheets_resource

        google_sheets_resource_def = ResourceDefinition(
            resource_fn=google_sheets_resource_fn
        )
        context = build_op_context(
            resources={"feature_flags_google_sheet": google_sheets_resource_def}
        )

        context.log.info = MagicMock()
        context.log.error = MagicMock()

        result = sync_flags_to_sheets(context, mock_df)

        # Verify worksheet was created
        mock_sheet.worksheet.assert_called_once_with("Feature Flags")
        mock_sheet.add_worksheet.assert_called_once_with(
            title="Feature Flags", rows=1000, cols=20
        )
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once()

        assert result is None

    def test_sync_flags_to_sheets_adds_synced_at_column(self):
        """Test that synced_at timestamp is added to the dataframe."""
        mock_df = pl.DataFrame(
            {
                "id": [1],
                "flag_name": ["enable_feature_a"],
                "enabled": [True],
            }
        )

        mock_google_sheets_resource = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_google_sheets_resource.get_sheet.return_value = mock_sheet

        def google_sheets_resource_fn(_context):
            return mock_google_sheets_resource

        google_sheets_resource_def = ResourceDefinition(
            resource_fn=google_sheets_resource_fn
        )
        context = build_op_context(
            resources={"feature_flags_google_sheet": google_sheets_resource_def}
        )

        context.log.info = MagicMock()
        context.log.error = MagicMock()

        sync_flags_to_sheets(context, mock_df)

        # Verify synced_at column was added
        update_call_args = mock_worksheet.update.call_args
        all_rows = update_call_args[0][1]
        headers = all_rows[0]

        assert "synced_at" in headers
        assert len(headers) == 4  # id, flag_name, enabled, synced_at

    def test_sync_flags_to_sheets_casts_to_strings(self):
        """Test that all columns are cast to strings for Google Sheets compatibility."""
        mock_df = pl.DataFrame(
            {
                "id": [1, 2],
                "flag_name": ["enable_feature_a", "enable_feature_b"],
                "enabled": [True, False],
            }
        )

        mock_google_sheets_resource = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_google_sheets_resource.get_sheet.return_value = mock_sheet

        def google_sheets_resource_fn(_context):
            return mock_google_sheets_resource

        google_sheets_resource_def = ResourceDefinition(
            resource_fn=google_sheets_resource_fn
        )
        context = build_op_context(
            resources={"feature_flags_google_sheet": google_sheets_resource_def}
        )

        context.log.info = MagicMock()
        context.log.error = MagicMock()

        sync_flags_to_sheets(context, mock_df)

        # Verify data was cast to strings
        update_call_args = mock_worksheet.update.call_args
        all_rows = update_call_args[0][1]
        data_rows = all_rows[1:]  # Skip header row

        # All values should be strings (including boolean True/False)
        for row in data_rows:
            for value in row:
                assert isinstance(value, str)

    def test_sync_flags_to_sheets_handles_empty_dataframe(self):
        """Test handling of empty dataframe."""
        mock_df = pl.DataFrame(
            {
                "id": [],
                "flag_name": [],
                "enabled": [],
            }
        )

        mock_google_sheets_resource = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_google_sheets_resource.get_sheet.return_value = mock_sheet

        def google_sheets_resource_fn(_context):
            return mock_google_sheets_resource

        google_sheets_resource_def = ResourceDefinition(
            resource_fn=google_sheets_resource_fn
        )
        context = build_op_context(
            resources={"feature_flags_google_sheet": google_sheets_resource_def}
        )

        context.log.info = MagicMock()
        context.log.error = MagicMock()

        result = sync_flags_to_sheets(context, mock_df)

        # Should still clear and update (with just headers)
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once()

        update_call_args = mock_worksheet.update.call_args
        all_rows = update_call_args[0][1]
        assert len(all_rows) == 1  # Just headers, no data rows

        assert result is None

    def test_sync_flags_to_sheets_raises_error_on_exception(self):
        """Test that errors are logged and re-raised."""
        mock_df = pl.DataFrame(
            {
                "id": [1],
                "flag_name": ["enable_feature_a"],
                "enabled": [True],
            }
        )

        mock_google_sheets_resource = MagicMock()
        mock_google_sheets_resource.get_sheet.side_effect = Exception(
            "Google API Error"
        )

        def google_sheets_resource_fn(_context):
            return mock_google_sheets_resource

        google_sheets_resource_def = ResourceDefinition(
            resource_fn=google_sheets_resource_fn
        )
        context = build_op_context(
            resources={"feature_flags_google_sheet": google_sheets_resource_def}
        )

        context.log.info = MagicMock()
        context.log.error = MagicMock()

        with pytest.raises(Exception, match="Google API Error"):
            sync_flags_to_sheets(context, mock_df)

        # Verify error was logged
        context.log.error.assert_called_once()
        error_call = context.log.error.call_args[0][0]
        assert "Error syncing to Google Sheets" in error_call
