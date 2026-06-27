import polars as pl
import pytest

from dagster_project.gates import GateError, check_for_nulls, check_min_rows


@pytest.mark.unit
def test_check_for_nulls_returns_zero_when_column_has_no_nulls():
    df = pl.DataFrame(
        {
            "source_id": ["a", "b", "c"],
            "value": [1, 2, 3],
        }
    )

    assert check_for_nulls(df, column="source_id") == 0


@pytest.mark.unit
def test_check_for_nulls_raises_for_missing_column():
    df = pl.DataFrame({"value": [1, 2, 3]})

    with pytest.raises(
        GateError,
        match="required column 'source_id' missing from batch",
    ):
        check_for_nulls(df, column="source_id")


@pytest.mark.unit
def test_check_for_nulls_raises_when_column_contains_nulls():
    df = pl.DataFrame(
        {
            "source_id": ["a", None, "c", None],
            "value": [1, 2, 3, 4],
        }
    )

    with pytest.raises(
        GateError,
        match="column 'source_id' contains 2 null value\\(s\\)",
    ):
        check_for_nulls(df, column="source_id")


@pytest.mark.unit
def test_check_min_rows_returns_row_count_when_floor_is_met():
    df = pl.DataFrame({"value": [1, 2]})

    assert check_min_rows(df, min_rows=2) == 2


@pytest.mark.unit
def test_check_min_rows_allows_zero_floor():
    df = pl.DataFrame({"value": []}, schema={"value": pl.Int64})

    assert check_min_rows(df, min_rows=0) == 0


@pytest.mark.unit
def test_check_min_rows_raises_when_below_floor():
    df = pl.DataFrame({"value": []}, schema={"value": pl.Int64})

    with pytest.raises(GateError, match="row count 0 below floor 1"):
        check_min_rows(df)


@pytest.mark.unit
def test_check_min_rows_rejects_negative_floor():
    df = pl.DataFrame({"value": [1]})

    with pytest.raises(ValueError, match="min_rows must be non-negative"):
        check_min_rows(df, min_rows=-1)
