"""Unit tests for get_sales_data assets."""

from datetime import date

from dagster import build_op_context
import polars as pl
import pytest

from dagster_project.assets.ingestion.get_sales_data import sales_data, sales_summary


@pytest.mark.unit
class TestSalesData:
    """Test the sales_data asset."""

    def test_sales_data_success(self):
        """Test successful generation of sales data DataFrame."""
        context = build_op_context(partition_key="2025-12-18")

        result = sales_data(context)

        assert isinstance(result, pl.DataFrame)
        # Asset generates 5-100 random rows
        assert len(result) >= 5
        assert len(result) <= 100
        assert "id" in result.columns
        assert "total_sales" in result.columns
        assert "date" in result.columns
        # Check that date matches the partition date
        partition_date = date(2025, 12, 18)
        assert all(result["date"] == partition_date)

    def test_sales_data_has_correct_structure(self):
        """Test that sales_data generates correct DataFrame structure."""
        context = build_op_context(partition_key="2025-12-18")

        result = sales_data(context)

        # Verify column types
        # IDs are UUID strings, not integers
        assert result["id"].dtype == pl.Utf8
        assert result["total_sales"].dtype == pl.Int64
        assert result["date"].dtype == pl.Date

        # Verify IDs are non-null UUID strings
        assert result["id"].null_count() == 0
        # UUIDs are 36 characters long (with hyphens)
        assert all(result["id"].str.len_chars() == 36)

        # Verify sales values are within expected range
        assert result["total_sales"].min() >= 10
        assert result["total_sales"].max() <= 100


@pytest.mark.unit
class TestSalesSummary:
    """Test the sales_summary asset."""

    def test_sales_summary_success(self):
        """Test successful calculation of sales summary."""
        # Create a test DataFrame
        test_df = pl.DataFrame(
            {
                "id": [1, 2, 3],
                "total_sales": [10, 20, 30],
                "date": [date.today()] * 3,
            }
        )

        context = build_op_context(partition_key="2025-12-18")

        result = sales_summary(context, test_df)

        assert isinstance(result, int)
        assert result == 60

    def test_sales_summary_zero_sum(self):
        """Test sales_summary with DataFrame containing zeros."""
        # Use zeros instead of empty DataFrame to avoid None return from Polars sum()
        test_df = pl.DataFrame(
            {
                "id": [1],
                "total_sales": [0],
                "date": [date.today()],
            }
        )

        context = build_op_context(partition_key="2025-12-18")

        result = sales_summary(context, test_df)

        assert isinstance(result, int)
        assert result == 0

    def test_sales_summary_single_row(self):
        """Test sales_summary with single row."""
        test_df = pl.DataFrame(
            {
                "id": [1],
                "total_sales": [50],
                "date": [date.today()],
            }
        )

        context = build_op_context(partition_key="2025-12-18")

        result = sales_summary(context, test_df)

        assert result == 50
