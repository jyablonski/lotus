import polars as pl
import random
from datetime import date
from dagster import asset, AssetExecutionContext


@asset
def sales_data(context: AssetExecutionContext) -> pl.DataFrame:
    """Generate a DataFrame with 10 rows of sales data."""
    df = pl.DataFrame(
        {
            "id": range(1, 11),
            "total_sales": [random.randint(10, 100) for _ in range(10)],
            "date": [date.today()] * 10,
        }
    )
    context.log.info(f"Generated DataFrame:\n{df}")
    return df


# Dagster infers the dependency from the function parameter name.
@asset
def sales_summary(context: AssetExecutionContext, sales_data: pl.DataFrame) -> int:
    """Sum the total_sales field."""
    total = sales_data["total_sales"].sum()
    context.log.info(f"Total sales: {total}")
    return total
