from datetime import date

from dagster import build_op_context
import polars as pl
import pytest

from dagster_project.defs.assets.ingestion import get_sales_data as sales_data_module
from dagster_project.defs.assets.ingestion.get_sales_data import (
    SALES_TABLE_NAME,
    sales_data,
    sales_data_bronze,
)
from dagster_project.gates import GateError


class FakePostgresResource:
    def __init__(self):
        self.write_kwargs = None

    def write_to_postgres(self, **kwargs):
        self.write_kwargs = kwargs
        return kwargs["df"].height


@pytest.mark.unit
class TestSalesData:
    def test_sales_data_success(self):
        context = build_op_context(partition_key="2025-12-18")

        df = sales_data(context)

        assert isinstance(df, pl.DataFrame)
        # Asset generates 5-100 random rows
        assert len(df) >= 5
        assert len(df) <= 100
        assert "id" in df.columns
        assert "total_sales" in df.columns
        assert "date" in df.columns
        partition_date = date(2025, 12, 18)
        assert all(df["date"] == partition_date)

    def test_sales_data_has_correct_structure(self):
        context = build_op_context(partition_key="2025-12-18")

        result = sales_data(context)

        # IDs are UUID strings, not integers
        assert result["id"].dtype == pl.Utf8
        assert result["total_sales"].dtype == pl.Int64
        assert result["date"].dtype == pl.Date

        assert result["id"].null_count() == 0
        # UUIDs are 36 characters long (with hyphens)
        assert all(result["id"].str.len_chars() == 36)

        assert result["total_sales"].min() >= 10
        assert result["total_sales"].max() <= 100

    def test_sales_data_runs_fail_fast_gates(self, monkeypatch):
        context = build_op_context(partition_key="2025-12-18")
        calls = {}

        def fake_check_min_rows(df, min_rows=1):
            calls["min_rows"] = min_rows
            calls["row_count"] = df.height
            return df.height

        def fake_check_for_nulls(df, column):
            calls["null_column"] = column
            calls["null_row_count"] = df.height
            return 0

        monkeypatch.setattr(sales_data_module, "check_min_rows", fake_check_min_rows)
        monkeypatch.setattr(sales_data_module, "check_for_nulls", fake_check_for_nulls)

        result = sales_data(context)

        assert calls == {
            "min_rows": 1,
            "row_count": result.height,
            "null_column": "id",
            "null_row_count": result.height,
        }

    def test_sales_data_propagates_min_row_gate_failure(self, monkeypatch):
        context = build_op_context(partition_key="2025-12-18")

        def fake_randint(_start, _end):
            return 0

        monkeypatch.setattr(sales_data_module.random, "randint", fake_randint)

        with pytest.raises(GateError, match="row count 0 below floor 1"):
            sales_data(context)

    def test_sales_data_bronze_writes_to_postgres(self):
        context = build_op_context(partition_key="2025-12-18")
        df = pl.DataFrame(
            {
                "id": ["sales-1", "sales-2"],
                "total_sales": [12, 34],
                "date": [date(2025, 12, 18), date(2025, 12, 18)],
            }
        )
        fake_postgres = FakePostgresResource()

        sales_data_bronze(
            context,
            sales_data=df,
            postgres_conn=fake_postgres,
        )

        assert fake_postgres.write_kwargs is not None
        assert fake_postgres.write_kwargs["df"] is df
        assert fake_postgres.write_kwargs["table_name"] == SALES_TABLE_NAME
        assert fake_postgres.write_kwargs["schema"] == "source"
        assert fake_postgres.write_kwargs["conflict_columns"] == ["id"]
