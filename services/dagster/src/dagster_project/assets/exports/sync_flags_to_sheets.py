from datetime import datetime, timezone

from dagster import AssetExecutionContext, asset
import gspread
import polars as pl

from dagster_project.resources import PostgresResource, GoogleSheetsResource


@asset(group_name="exports")
def get_feature_flags_from_postgres(
    context: AssetExecutionContext,
    postgres_conn: PostgresResource,
) -> pl.DataFrame:
    """Read feature flags data from source.feature_flags postgres table."""
    with postgres_conn.get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM feature_flags")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    df = pl.DataFrame(rows, schema=columns, orient="row")

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

    # Cast all columns to strings for Google Sheets compatibility
    df_strings = df_with_timestamp.cast(
        {col: pl.Utf8 for col in df_with_timestamp.columns}
    )

    try:
        sheet = feature_flags_google_sheet.get_sheet()
        try:
            worksheet = sheet.worksheet("Feature Flags")
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="Feature Flags", rows=1000, cols=20)

        headers = df_strings.columns
        rows = df_strings.rows()
        all_rows = [headers] + list(rows)

        worksheet.clear()
        worksheet.update("A1", all_rows, value_input_option="RAW")

        context.log.info(
            f"Synced {len(df_strings)} feature flags to Google Sheets at {synced_at}"
        )
    except Exception as e:
        context.log.error(f"Error syncing to Google Sheets: {e}")
        raise
