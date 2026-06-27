from datetime import timedelta

from dagster import AssetExecutionContext, FreshnessPolicy, asset
import polars as pl

from dagster_project.resources import PostgresResource
from dagster_project.sql.exports import SELECT_USER_JOURNAL_SUMMARY


@asset(
    group_name="exports",
    owners=["team:data-engineering"],
    # Task-level retries: if this specific asset fails, retry it N times within the same run.
    # retry_policy=RetryPolicy(max_retries=2, delay=30),
    freshness_policy=FreshnessPolicy.time_window(fail_window=timedelta(hours=24)),
)
def unload_journals_to_s3(
    context: AssetExecutionContext,
    postgres_conn: PostgresResource,
) -> pl.DataFrame:
    """Pull data from postgres.core.fct_journal_entries into a Polars dataframe."""
    df = postgres_conn.query_to_polars(SELECT_USER_JOURNAL_SUMMARY)

    context.log.info(f"Total rows: {len(df)}")
    context.log.info(f"First 10 rows:\n{df.head(10)}")

    context.add_output_metadata(
        {
            "num_rows": len(df),
            "columns": df.columns,
        }
    )

    return df
