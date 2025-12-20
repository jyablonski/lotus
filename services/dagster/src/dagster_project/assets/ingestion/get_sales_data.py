import random
import uuid

from dagster import (
    AssetCheckExecutionContext,
    AssetCheckResult,
    AssetExecutionContext,
    DailyPartitionsDefinition,
    asset,
    asset_check,
)
import polars as pl

from dagster_project.assets.ingestion.utils import (
    create_basic_metadata,
    create_summary_metadata,
    get_partition_date,
    get_partition_date_str,
)

# Define daily partitions starting from today
daily_partitions = DailyPartitionsDefinition(start_date="2025-12-18")


@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_data(context: AssetExecutionContext) -> pl.DataFrame:
    """Generate a DataFrame with 5-100 rows of sales data for the partition date."""
    # Get the partition date from the context
    partition_date = get_partition_date(context)
    partition_date_str = get_partition_date_str(context)

    # Generate random number of rows between 5-100
    num_rows = random.randint(5, 100)

    # Generate UUIDs for uniqueness
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

    # Add metadata for observability
    context.add_output_metadata(create_basic_metadata(context, num_rows=num_rows, df=df))

    return df


@asset_check(asset=sales_data, name="sales_data_asset_check", blocking=True)
def sales_data_asset_check(
    context: AssetCheckExecutionContext, sales_data: pl.DataFrame
) -> AssetCheckResult:
    """Check that total sales fall within 10-100 and no IDs are null."""
    # Check that total_sales values are within 10-100 range
    sales_values = sales_data["total_sales"]
    min_sales = sales_values.min()
    max_sales = sales_values.max()
    sales_in_range = (min_sales >= 10) and (max_sales <= 100)

    # Check that no IDs are null
    id_column = sales_data["id"]
    null_ids = id_column.null_count()
    no_null_ids = null_ids == 0

    passed = sales_in_range and no_null_ids

    if not passed:
        issues = []
        if not sales_in_range:
            issues.append(
                f"Sales values out of range: min={min_sales}, max={max_sales} (expected 10-100)"
            )
        if not no_null_ids:
            issues.append(f"Found {null_ids} null ID(s)")
        context.log.error(f"Asset check failed: {'; '.join(issues)}")
    else:
        context.log.info(f"Asset check passed: sales range [{min_sales}, {max_sales}], no null IDs")

    return AssetCheckResult(passed=passed)


# Dagster infers the dependency from the function parameter name.
# sales_summary inherits partitions from sales_data automatically
@asset(group_name="ingestion", partitions_def=daily_partitions)
def sales_summary(context: AssetExecutionContext, sales_data: pl.DataFrame) -> int:
    """Sum the total_sales field for the partition."""
    partition_date_str = get_partition_date_str(context)
    total = sales_data["total_sales"].sum()
    context.log.info(f"Total sales for partition {partition_date_str}: {total}")

    context.add_output_metadata(
        create_summary_metadata(context, total_sales=float(total), df=sales_data)
    )

    return total
