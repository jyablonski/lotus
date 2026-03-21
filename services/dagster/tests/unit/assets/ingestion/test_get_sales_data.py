"""Unit tests for get_sales_data assets."""

from datetime import date

from dagster import build_op_context
import polars as pl
import pytest

from dagster_project.assets.ingestion.get_sales_data import sales_data


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
