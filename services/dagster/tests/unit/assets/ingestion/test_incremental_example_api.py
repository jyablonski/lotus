from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from dagster import ResourceDefinition, build_op_context
import pytest

from dagster_project.assets.ingestion.incremental_example_api import (
    PAGE_SIZE,
    SAFETY_LOOKBACK,
    SOURCE_NAME,
    _context_run_id,
    example_api_records_incremental,
)
from dagster_project.sql.ingestion import SELECT_INGESTION_WATERMARK_FOR_UPDATE


def _mock_cursor(mock_postgres_resource):
    mock_conn = (
        mock_postgres_resource.get_connection.return_value.__enter__.return_value
    )
    return mock_conn.cursor.return_value.__enter__.return_value


def _execute_calls_for(mock_cursor, query: str):
    return [
        call_args
        for call_args in mock_cursor.execute.call_args_list
        if call_args.args and call_args.args[0] == query
    ]


def _resource_def(resource):
    return ResourceDefinition(resource_fn=lambda _context: resource)


@pytest.mark.unit
class TestIncrementalExampleApi:
    def test_asset_pages_from_watermark_and_advances_cursor(
        self, mock_postgres_resource
    ):
        existing_watermark = datetime(2026, 4, 17, 6, 0, tzinfo=UTC)
        mock_cursor = _mock_cursor(mock_postgres_resource)
        mock_cursor.fetchone.return_value = (existing_watermark,)

        api_client = MagicMock()
        api_client.fetch_modified_records.side_effect = [
            (
                [
                    {
                        "id": "example-001",
                        "status": "created",
                        "modified_at": "2026-04-17T06:01:00Z",
                    }
                ],
                "1",
            ),
            (
                [
                    {
                        "id": "example-002",
                        "status": "updated",
                        "modified_at": "2026-04-17T07:15:00+00:00",
                    }
                ],
                None,
            ),
        ]

        with build_op_context(
            resources={
                "api_client": _resource_def(api_client),
                "postgres_conn": _resource_def(mock_postgres_resource),
            }
        ) as context:
            example_api_records_incremental(context)

            final_run_id = _context_run_id(context)

        assert api_client.fetch_modified_records.call_count == 2
        first_page_kwargs = api_client.fetch_modified_records.call_args_list[0].kwargs
        second_page_kwargs = api_client.fetch_modified_records.call_args_list[1].kwargs
        assert first_page_kwargs["modified_at_gte"] == (
            existing_watermark - SAFETY_LOOKBACK
        )
        assert first_page_kwargs["page_token"] is None
        assert first_page_kwargs["page_size"] == PAGE_SIZE
        assert second_page_kwargs["page_token"] == "1"

        assert mock_postgres_resource.write_to_postgres.call_count == 4
        init_df = mock_postgres_resource.write_to_postgres.call_args_list[0].kwargs[
            "df"
        ]
        assert init_df["source_name"].to_list() == [SOURCE_NAME]
        assert init_df["watermark_at"].to_list() == [datetime(1970, 1, 1, tzinfo=UTC)]

        init_kwargs = mock_postgres_resource.write_to_postgres.call_args_list[0].kwargs
        assert init_kwargs["conflict_columns"] == ["source_name"]
        assert init_kwargs["update_columns"] == []
        assert init_kwargs["cursor"] == mock_cursor

        first_df = mock_postgres_resource.write_to_postgres.call_args_list[1].kwargs[
            "df"
        ]
        assert first_df.columns == ["source_id", "payload", "modified_at"]
        assert first_df["source_id"].to_list() == ["example-001"]
        assert first_df["payload"].to_list()[0]["status"] == "created"

        write_kwargs = mock_postgres_resource.write_to_postgres.call_args_list[1].kwargs
        assert write_kwargs["table_name"] == "example_api_records"
        assert write_kwargs["conflict_columns"] == ["source_id"]
        assert write_kwargs["json_columns"] == ["payload"]
        assert write_kwargs["cursor"] == mock_cursor

        final_df = mock_postgres_resource.write_to_postgres.call_args_list[-1].kwargs[
            "df"
        ]
        assert final_df["source_name"].to_list() == [SOURCE_NAME]
        assert final_df["watermark_at"].to_list()[0] > existing_watermark
        assert final_df["last_run_id"].to_list() == [final_run_id]

        watermark_reads = _execute_calls_for(
            mock_cursor, SELECT_INGESTION_WATERMARK_FOR_UPDATE
        )
        assert len(watermark_reads) == 1

        mock_conn = (
            mock_postgres_resource.get_connection.return_value.__enter__.return_value
        )
        mock_conn.commit.assert_called_once()

    def test_asset_advances_watermark_when_no_records(self, mock_postgres_resource):
        existing_watermark = datetime.now(UTC) - timedelta(days=1)
        mock_cursor = _mock_cursor(mock_postgres_resource)
        mock_cursor.fetchone.return_value = (existing_watermark,)

        api_client = MagicMock()
        api_client.fetch_modified_records.return_value = ([], None)

        with build_op_context(
            resources={
                "api_client": _resource_def(api_client),
                "postgres_conn": _resource_def(mock_postgres_resource),
            }
        ) as context:
            example_api_records_incremental(context)

        assert mock_postgres_resource.write_to_postgres.call_count == 2
        init_kwargs = mock_postgres_resource.write_to_postgres.call_args_list[0].kwargs
        assert init_kwargs["update_columns"] == []

        final_df = mock_postgres_resource.write_to_postgres.call_args_list[-1].kwargs[
            "df"
        ]
        assert final_df["source_name"].to_list() == [SOURCE_NAME]
        assert final_df["watermark_at"].to_list()[0] > existing_watermark

        mock_conn = (
            mock_postgres_resource.get_connection.return_value.__enter__.return_value
        )
        mock_conn.commit.assert_called_once()
