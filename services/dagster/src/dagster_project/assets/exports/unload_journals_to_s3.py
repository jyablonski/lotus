from dagster import AssetExecutionContext, asset
import polars as pl

from dagster_project.resources import PostgresResource


@asset(group_name="exports")
def unload_journals_to_s3(
    context: AssetExecutionContext,
    postgres_conn: PostgresResource,
) -> pl.DataFrame:
    """Pull data from postgres.core.fct_journal_entries into a Polars dataframe."""
    with postgres_conn.get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM gold.user_journal_summary")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    df = pl.DataFrame(rows, schema=columns, orient="row")

    # Print first 10 rows
    context.log.info(f"Total rows: {len(df)}")
    context.log.info(f"First 10 rows:\n{df.head(10)}")

    return df
