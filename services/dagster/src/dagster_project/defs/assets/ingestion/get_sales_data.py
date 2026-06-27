import random
from typing import Any, cast
import uuid

from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    asset,
)
import polars as pl

from dagster_project.defs.assets.ingestion.utils import (
    create_basic_metadata,
    get_partition_date,
    get_partition_date_str,
)
from dagster_project.gates import check_for_nulls, check_min_rows
from dagster_project.resources import PostgresResource

# Define daily partitions starting from today
daily_partitions = DailyPartitionsDefinition(start_date="2025-12-18")
SALES_TABLE_NAME = "sales_data"


@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_data(context: AssetExecutionContext) -> pl.DataFrame:
    """Generate and gate the partition's sales data, held in memory for the bronze load."""
    partition_date = get_partition_date(context)
    partition_date_str = get_partition_date_str(context)

    num_rows = random.randint(5, 100)
    ids = [str(uuid.uuid4()) for _ in range(num_rows)]

    df = pl.DataFrame(
        {
            "id": ids,
            "total_sales": [random.randint(10, 100) for _ in range(num_rows)],
            "date": [partition_date] * num_rows,
        }
    )
    context.log.info(
        f"Generated DataFrame with {num_rows} rows for partition {partition_date_str}:\n{df}"
    )

    row_count = check_min_rows(df)
    check_for_nulls(df, column="id")

    # Validate generated sales values stay within the expected demo range.
    min_sales = int(cast(Any, df["total_sales"].min()))
    max_sales = int(cast(Any, df["total_sales"].max()))
    if min_sales < 10 or max_sales > 100:
        raise ValueError(
            "Data quality check failed: "
            f"Sales out of range: min={min_sales}, max={max_sales} (expected 10-100)"
        )

    total_sales = df["total_sales"].sum()
    context.add_output_metadata(
        {
            **create_basic_metadata(context, num_rows=row_count, df=df),
            "total_sales": float(total_sales),
        }
    )

    return df


@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_data_bronze(
    context: AssetExecutionContext,
    sales_data: pl.DataFrame,
    postgres_conn: PostgresResource,
) -> None:
    """Load the partition's gated sales data into bronze Postgres."""
    written_rows = postgres_conn.write_to_postgres(
        df=sales_data,
        table_name=SALES_TABLE_NAME,
        schema="source",
        conflict_columns=["id"],
    )

    context.log.info(
        f"Loaded {written_rows} sales row(s) into source.{SALES_TABLE_NAME}"
    )
    context.add_output_metadata(
        create_basic_metadata(context, num_rows=written_rows, df=sales_data)
    )
