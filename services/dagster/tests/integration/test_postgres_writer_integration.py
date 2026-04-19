"""Integration tests for the PostgresResource Polars writer."""

from datetime import UTC, datetime

import polars as pl
import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestPostgresWriterIntegration:
    def test_write_to_postgres_inserts_and_upserts_polars_dataframe(
        self,
        postgres_resource_with_source_schema,
    ):
        initial_df = pl.DataFrame(
            {
                "source_id": ["example-001", "example-002"],
                "payload": [{"team": "math"}, {"team": "systems"}],
                "modified_at": [
                    datetime(2026, 4, 17, 6, 0, tzinfo=UTC),
                    datetime(2026, 4, 17, 7, 0, tzinfo=UTC),
                ],
            }
        )

        inserted_count = postgres_resource_with_source_schema.write_to_postgres(
            df=initial_df,
            table_name="example_api_records",
            conflict_columns=["source_id"],
            json_columns=["payload"],
        )
        assert inserted_count == 2

        update_df = pl.DataFrame(
            {
                "source_id": ["example-001"],
                "payload": [{"team": "analytics", "level": "principal"}],
                "modified_at": [datetime(2026, 4, 18, 6, 0, tzinfo=UTC)],
            }
        )

        updated_count = postgres_resource_with_source_schema.write_to_postgres(
            df=update_df,
            table_name="example_api_records",
            conflict_columns=["source_id"],
            json_columns=["payload"],
        )
        assert updated_count == 1

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
            rows = cur.fetchall()

        assert len(rows) == 2
        assert rows[0][0] == "example-001"
        assert rows[0][1] == {"team": "analytics", "level": "principal"}
        assert rows[0][2] == datetime(2026, 4, 18, 6, 0, tzinfo=UTC)
        assert rows[1][0] == "example-002"
        assert rows[1][1] == {"team": "systems"}
