from dataclasses import dataclass
from datetime import UTC, datetime, time
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
from dagster_project.resources import PostgresResource, S3Resource

# Define daily partitions starting from today
daily_partitions = DailyPartitionsDefinition(start_date="2025-12-18")
SALES_TABLE_NAME = "sales_data"


@dataclass(frozen=True)
class SalesDataExtractResult:
    s3_key: str
    row_count: int
    total_sales: float


@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_data(
    context: AssetExecutionContext,
    s3_resource: S3Resource,
) -> SalesDataExtractResult:
    """Generate, gate, and persist the partition's sales data to S3."""
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
    partition_dt = datetime.combine(partition_date, time.min, tzinfo=UTC)
    s3_key = s3_resource.write_parquet(
        df,
        SALES_TABLE_NAME,
        partition_dt=partition_dt,
    )

    context.add_output_metadata(
        {
            **create_basic_metadata(context, num_rows=row_count, df=df),
            "total_sales": float(total_sales),
            "s3_key": s3_key,
        }
    )

    return SalesDataExtractResult(
        s3_key=s3_key,
        row_count=row_count,
        total_sales=float(total_sales),
    )


@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_data_bronze(
    context: AssetExecutionContext,
    sales_data: SalesDataExtractResult,
    s3_resource: S3Resource,
    postgres_conn: PostgresResource,
) -> None:
    """Copy the partition's persisted sales data from S3 into bronze Postgres."""
    df = s3_resource.read_parquet(sales_data.s3_key)
    written_rows = postgres_conn.write_to_postgres(
        df=df,
        table_name=SALES_TABLE_NAME,
        schema="bronze",
        conflict_columns=["id"],
    )

    context.log.info(
        f"Copied {written_rows} sales row(s) from s3://{s3_resource.bucket}/{sales_data.s3_key}"
    )
    context.add_output_metadata(
        {
            **create_basic_metadata(context, num_rows=written_rows, df=df),
            "s3_key": sales_data.s3_key,
        }
    )
