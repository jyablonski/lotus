from datetime import datetime

from dagster import AssetExecutionContext, MetadataValue
import polars as pl


def get_partition_date(context: AssetExecutionContext) -> datetime.date:
    """Extract the partition date from the asset execution context.

    Args:
        context: The asset execution context

    Returns:
        The partition date as a date object
    """
    partition_date_str = context.partition_key
    return datetime.strptime(partition_date_str, "%Y-%m-%d").date()


def get_partition_date_str(context: AssetExecutionContext) -> str:
    """Extract the partition date string from the asset execution context.

    Args:
        context: The asset execution context

    Returns:
        The partition date as a string (YYYY-MM-DD format)
    """
    return context.partition_key


def extract_date_range(df: pl.DataFrame, date_column: str = "date") -> str:
    """Extract date range from a DataFrame's date column.

    Args:
        df: The DataFrame containing date information
        date_column: Name of the date column (default: "date")

    Returns:
        A string representation of the date range (e.g., "2025-01-01 to 2025-01-31" or "2025-01-01")
    """
    min_date = df[date_column].min()
    max_date = df[date_column].max()
    return f"{min_date} to {max_date}" if min_date != max_date else str(min_date)


def create_basic_metadata(
    context: AssetExecutionContext,
    num_rows: int | None = None,
    date_range: str | None = None,
    df: pl.DataFrame | None = None,
    date_column: str = "date",
) -> dict[str, MetadataValue]:
    """Create a basic metadata dictionary with common fields.

    Args:
        context: The asset execution context
        num_rows: Number of rows (if None and df provided, will be calculated)
        date_range: Date range string (if None and df provided, will be calculated)
        df: Optional DataFrame to extract metadata from
        date_column: Name of the date column if extracting from DataFrame

    Returns:
        A dictionary of metadata values
    """
    metadata = {
        "partition": MetadataValue.text(get_partition_date_str(context)),
    }

    # Extract num_rows from DataFrame if not provided
    if num_rows is None and df is not None:
        num_rows = len(df)

    if num_rows is not None:
        metadata["num_rows"] = MetadataValue.int(num_rows)

    # Extract date_range from DataFrame if not provided
    if date_range is None and df is not None and date_column in df.columns:
        date_range = extract_date_range(df, date_column)

    if date_range is not None:
        metadata["date_range"] = MetadataValue.text(date_range)

    return metadata


def create_summary_metadata(
    context: AssetExecutionContext,
    total_sales: float | None = None,
    num_rows: int | None = None,
    df: pl.DataFrame | None = None,
) -> dict[str, MetadataValue]:
    """Create metadata dictionary for summary assets.

    Args:
        context: The asset execution context
        total_sales: Total sales value
        num_rows: Number of rows (if None and df provided, will be calculated)
        df: Optional DataFrame to extract num_rows from

    Returns:
        A dictionary of metadata values
    """
    metadata = {
        "partition": MetadataValue.text(get_partition_date_str(context)),
    }

    if total_sales is not None:
        metadata["total_sales"] = MetadataValue.float(float(total_sales))

    # Extract num_rows from DataFrame if not provided
    if num_rows is None and df is not None:
        num_rows = len(df)

    if num_rows is not None:
        metadata["num_rows"] = MetadataValue.int(num_rows)

    return metadata
