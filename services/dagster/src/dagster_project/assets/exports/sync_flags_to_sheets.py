from datetime import datetime, timezone

from dagster import AssetExecutionContext, asset
import polars as pl

from dagster_project.resources import GoogleSheetsResource, PostgresResource
from dagster_project.sql.exports import SELECT_FEATURE_FLAGS


@asset(group_name="exports")
def get_feature_flags_from_postgres(
    context: AssetExecutionContext,
    postgres_conn: PostgresResource,
) -> pl.DataFrame:
    """Read feature flags data from source.feature_flags postgres table."""
    df = postgres_conn.query_to_polars(SELECT_FEATURE_FLAGS)

    context.log.info(f"Fetched {len(df)} feature flags from Postgres")
    context.log.info(f"Columns: {df.columns}")

    return df


@asset(group_name="exports")
def sync_flags_to_sheets(
    context: AssetExecutionContext,
    get_feature_flags_from_postgres: pl.DataFrame,
    feature_flags_google_sheet: GoogleSheetsResource,
) -> None:
    """Sync feature flags data to Google Sheets with synced_at timestamp."""
    synced_at = datetime.now(timezone.utc).isoformat()
    df_with_timestamp = get_feature_flags_from_postgres.with_columns(
        pl.lit(synced_at).alias("synced_at")
    )

    df_strings = df_with_timestamp.cast(
        {col: pl.Utf8 for col in df_with_timestamp.columns}
    )

    try:
        feature_flags_google_sheet.overwrite_with_rows(
            worksheet_name="Feature Flags",
            header=list(df_strings.columns),
            rows=[list(row) for row in df_strings.rows()],
        )
    except Exception as e:
        context.log.error(f"Error syncing to Google Sheets: {e}")
        raise

    context.log.info(
        f"Synced {len(df_strings)} feature flags to Google Sheets at {synced_at}"
    )
