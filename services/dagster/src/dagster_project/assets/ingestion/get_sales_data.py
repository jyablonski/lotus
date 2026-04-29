import random
from typing import Any, cast
import uuid

from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    asset,
)
import polars as pl

from dagster_project.assets.ingestion.utils import (
    create_basic_metadata,
    get_partition_date,
    get_partition_date_str,
)

# Define daily partitions starting from today
daily_partitions = DailyPartitionsDefinition(start_date="2025-12-18")


@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_data(context: AssetExecutionContext) -> pl.DataFrame:
    """Generate a DataFrame with 5-100 rows of sales data for the partition date."""
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

    # Validate: sales values in range and no null IDs
    min_sales = int(cast(Any, df["total_sales"].min()))
    max_sales = int(cast(Any, df["total_sales"].max()))
    null_ids = df["id"].null_count()
    if not ((min_sales >= 10) and (max_sales <= 100) and (null_ids == 0)):
        issues = []
        if not ((min_sales >= 10) and (max_sales <= 100)):
            issues.append(
                f"Sales out of range: min={min_sales}, max={max_sales} (expected 10-100)"
            )
        if null_ids > 0:
            issues.append(f"Found {null_ids} null ID(s)")
        raise ValueError(f"Data quality check failed: {'; '.join(issues)}")

    total_sales = df["total_sales"].sum()

    context.add_output_metadata(
        {
            **create_basic_metadata(context, num_rows=num_rows, df=df),
            "total_sales": float(total_sales),
        }
    )

    return df
