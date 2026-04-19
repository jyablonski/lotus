"""Integration tests for the incremental example API ingestion asset."""

from datetime import UTC, datetime

from dagster import build_asset_context
import pytest

from dagster_project.assets.ingestion import incremental_example_api
from dagster_project.assets.ingestion.incremental_example_api import (
    SOURCE_NAME,
    _context_run_id,
    example_api_records_incremental,
)
from dagster_project.resources.example_api import ApiClientResource


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 4, 18, 5, 0, tzinfo=tz or UTC)


@pytest.mark.integration
@pytest.mark.slow
class TestIncrementalExampleApiIntegration:
    def test_incremental_asset_writes_records_and_advances_watermark(
        self,
        monkeypatch,
        postgres_resource_with_source_schema,
    ):
        monkeypatch.setattr(incremental_example_api, "datetime", FixedDatetime)

        with build_asset_context(
            resources={
                "api_client": ApiClientResource(api_key="test-key", base_url=""),
                "postgres_conn": postgres_resource_with_source_schema,
            }
        ) as context:
            example_api_records_incremental(context)
            expected_run_id = _context_run_id(context)

            with (
                postgres_resource_with_source_schema.get_connection() as conn,
                conn.cursor() as cur,
            ):
                cur.execute(
                    """
                    SELECT source_id, payload, modified_at
                    FROM example_api_records
                    ORDER BY source_id
                    """
                )
                records = cur.fetchall()
                cur.execute(
                    """
                    SELECT source_name, watermark_at, last_run_id
                    FROM ingestion_watermarks
                    WHERE source_name = %s
                    """,
                    (SOURCE_NAME,),
                )
                watermark = cur.fetchone()

            assert [record[0] for record in records] == [
                "example-001",
                "example-002",
                "example-003",
                "example-004",
                "example-005",
            ]
            assert records[0][1]["name"] == "Ada Lovelace"
            assert records[-1][2] == datetime(2026, 4, 18, 4, 5, tzinfo=UTC)
            assert watermark == (
                SOURCE_NAME,
                datetime(2026, 4, 18, 5, 0, tzinfo=UTC),
                expected_run_id,
            )

            example_api_records_incremental(context)

            with (
                postgres_resource_with_source_schema.get_connection() as conn,
                conn.cursor() as cur,
            ):
                cur.execute("SELECT COUNT(*) FROM example_api_records")
                assert cur.fetchone()[0] == 5
