from datetime import date

from dagster import build_op_context
import polars as pl
import pytest

from dagster_project.defs.assets.ingestion import get_sales_data as sales_data_module
from dagster_project.defs.assets.ingestion.get_sales_data import (
    SALES_TABLE_NAME,
    SalesDataExtractResult,
    sales_data,
    sales_data_bronze,
)
from dagster_project.gates import GateError


class FakeS3Resource:
    bucket = "test-bucket"

    def __init__(self):
        self.written_df = None
        self.written_table_name = None
        self.written_partition_dt = None
        self.key = "sales_data/year=2025/month=12/day=18/sales_data.parquet"

    def write_parquet(self, df, table_name, *, partition_dt=None):
        self.written_df = df
        self.written_table_name = table_name
        self.written_partition_dt = partition_dt
        return self.key

    def read_parquet(self, key):
        if key != self.key:
            raise AssertionError(f"Unexpected S3 key: {key}")
        return self.written_df


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
        fake_s3 = FakeS3Resource()

        result = sales_data(context, s3_resource=fake_s3)

        assert isinstance(result, SalesDataExtractResult)
        assert result.s3_key == fake_s3.key
        assert fake_s3.written_df is not None
        assert result.row_count == fake_s3.written_df.height
        assert fake_s3.written_table_name == SALES_TABLE_NAME
        assert fake_s3.written_partition_dt.isoformat() == "2025-12-18T00:00:00+00:00"

        written_df = fake_s3.written_df
        assert isinstance(written_df, pl.DataFrame)
        # Asset generates 5-100 random rows
        assert len(written_df) >= 5
        assert len(written_df) <= 100
        assert "id" in written_df.columns
        assert "total_sales" in written_df.columns
        assert "date" in written_df.columns
        partition_date = date(2025, 12, 18)
        assert all(written_df["date"] == partition_date)

    def test_sales_data_has_correct_structure(self):
        context = build_op_context(partition_key="2025-12-18")
        fake_s3 = FakeS3Resource()

        sales_data(context, s3_resource=fake_s3)
        result = fake_s3.written_df

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
        fake_s3 = FakeS3Resource()
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

        result = sales_data(context, s3_resource=fake_s3)

        assert calls == {
            "min_rows": 1,
            "row_count": result.row_count,
            "null_column": "id",
            "null_row_count": result.row_count,
        }

    def test_sales_data_propagates_min_row_gate_failure(self, monkeypatch):
        context = build_op_context(partition_key="2025-12-18")
        fake_s3 = FakeS3Resource()

        def fake_randint(_start, _end):
            return 0

        monkeypatch.setattr(sales_data_module.random, "randint", fake_randint)

        with pytest.raises(GateError, match="row count 0 below floor 1"):
            sales_data(context, s3_resource=fake_s3)

    def test_sales_data_bronze_copies_s3_batch_to_bronze(self):
        context = build_op_context(partition_key="2025-12-18")
        fake_s3 = FakeS3Resource()
        fake_s3.written_df = pl.DataFrame(
            {
                "id": ["sales-1", "sales-2"],
                "total_sales": [12, 34],
                "date": [date(2025, 12, 18), date(2025, 12, 18)],
            }
        )
        fake_postgres = FakePostgresResource()
        extract_result = SalesDataExtractResult(
            s3_key=fake_s3.key,
            row_count=2,
            total_sales=46.0,
        )

        sales_data_bronze(
            context,
            sales_data=extract_result,
            s3_resource=fake_s3,
            postgres_conn=fake_postgres,
        )

        assert fake_postgres.write_kwargs is not None
        assert fake_postgres.write_kwargs["df"] is fake_s3.written_df
        assert fake_postgres.write_kwargs["table_name"] == SALES_TABLE_NAME
        assert fake_postgres.write_kwargs["schema"] == "bronze"
        assert fake_postgres.write_kwargs["conflict_columns"] == ["id"]
