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
        context = build_op_context()

        result = sales_data(context)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 10
        assert "id" in result.columns
        assert "total_sales" in result.columns
        assert "date" in result.columns
        assert all(result["date"] == date.today())

    def test_sales_data_has_correct_structure(self):
        """Test that sales_data generates correct DataFrame structure."""
        context = build_op_context()

        result = sales_data(context)

        # Verify column types
        assert result["id"].dtype == pl.Int64
        assert result["total_sales"].dtype == pl.Int64
        assert result["date"].dtype == pl.Date

        # Verify id range
        assert result["id"].min() == 1
        assert result["id"].max() == 10

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

        context = build_op_context()

        result = sales_summary(context, test_df)

        assert isinstance(result, int)
        assert result == 60

    def test_sales_summary_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        test_df = pl.DataFrame(
            {
                "id": [],
                "total_sales": [],
                "date": [],
            }
        )

        context = build_op_context()

        result = sales_summary(context, test_df)

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

        context = build_op_context()

        result = sales_summary(context, test_df)

        assert result == 50
