from datetime import UTC, datetime, timedelta
from typing import Any

from dagster import AssetExecutionContext, asset
from dagster._core.errors import DagsterInvalidPropertyError
import polars as pl

from dagster_project.resources import ApiClientResource, PostgresResource
from dagster_project.sql.ingestion import SELECT_INGESTION_WATERMARK_FOR_UPDATE

SOURCE_NAME = "example_api_records"
DEFAULT_WATERMARK = datetime(1970, 1, 1, tzinfo=UTC)
SAFETY_LOOKBACK = timedelta(minutes=5)
PAGE_SIZE = 100


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_modified_at(record: dict[str, Any]) -> datetime:
    modified_at = record.get("modified_at")
    if not isinstance(modified_at, str):
        raise ValueError("Example API record is missing a string modified_at field")

    parsed = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))
    return _coerce_utc(parsed)


def _source_id(record: dict[str, Any]) -> str:
    source_id = record.get("id")
    if source_id is None:
        raise ValueError("Example API record is missing an id field")
    return str(source_id)


def _records_to_dataframe(records: list[dict[str, Any]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "source_id": [_source_id(record) for record in records],
            "payload": records,
            "modified_at": [_parse_modified_at(record) for record in records],
        }
    )


def _watermark_dataframe(
    *, watermark_at: datetime, last_run_id: str | None
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "source_name": [SOURCE_NAME],
            "watermark_at": [_coerce_utc(watermark_at)],
            "updated_at": [datetime.now(UTC)],
            "last_run_id": [last_run_id],
        }
    )


def _context_run_id(context: AssetExecutionContext) -> str:
    try:
        return context.run.run_id
    except DagsterInvalidPropertyError:
        return "EPHEMERAL"


@asset(group_name="ingestion")
def example_api_records_incremental(
    context: AssetExecutionContext,
    api_client: ApiClientResource,
    postgres_conn: PostgresResource,
) -> None:
    """Incrementally ingest example API records by modified_at watermark."""
    upper_bound = datetime.now(UTC)
    page_token: str | None = None
    page_count = 0
    record_count = 0

    with postgres_conn.get_connection() as conn, conn.cursor() as cur:
        postgres_conn.write_to_postgres(
            df=_watermark_dataframe(watermark_at=DEFAULT_WATERMARK, last_run_id=None),
            table_name="ingestion_watermarks",
            conflict_columns=["source_name"],
            update_columns=[],
            cursor=cur,
        )
        cur.execute(SELECT_INGESTION_WATERMARK_FOR_UPDATE, (SOURCE_NAME,))
        row = cur.fetchone()
        if row is None:
            raise RuntimeError(f"Failed to initialize watermark for {SOURCE_NAME}")

        watermark_at = _coerce_utc(row[0])
        lower_bound = max(DEFAULT_WATERMARK, watermark_at - SAFETY_LOOKBACK)

        while True:
            records, page_token = api_client.fetch_modified_records(
                modified_at_gte=lower_bound,
                modified_at_lt=upper_bound,
                page_token=page_token,
                page_size=PAGE_SIZE,
            )
            page_count += 1

            if records:
                records_df = _records_to_dataframe(records)
                postgres_conn.write_to_postgres(
                    df=records_df,
                    table_name="example_api_records",
                    conflict_columns=["source_id"],
                    json_columns=["payload"],
                    cursor=cur,
                )

            record_count += len(records)
            if page_token is None:
                break

        postgres_conn.write_to_postgres(
            df=_watermark_dataframe(
                watermark_at=upper_bound,
                last_run_id=_context_run_id(context),
            ),
            table_name="ingestion_watermarks",
            conflict_columns=["source_name"],
            cursor=cur,
        )
        conn.commit()

    context.log.info(
        "Incremental example API ingestion completed: "
        f"{record_count} record(s), {page_count} page(s)"
    )
    context.add_output_metadata(
        {
            "source_name": SOURCE_NAME,
            "records": record_count,
            "pages": page_count,
            "previous_watermark": watermark_at.isoformat(),
            "lower_bound": lower_bound.isoformat(),
            "upper_bound": upper_bound.isoformat(),
        }
    )
