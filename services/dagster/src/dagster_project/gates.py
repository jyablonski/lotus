import polars as pl


class GateError(Exception):
    """Raised when a batch fails a hard, batch-level gate check."""


def check_for_nulls(
    df: pl.DataFrame,
    column: str,
) -> int:
    """Return null count, raising if any values in the column are null."""
    if column not in df.columns:
        raise GateError(f"required column {column!r} missing from batch")

    null_count = df[column].null_count()
    if null_count > 0:
        raise GateError(f"column {column!r} contains {null_count} null value(s)")
    return null_count


def check_min_rows(df: pl.DataFrame, min_rows: int = 1) -> int:
    """Return row count, raising if it is below the required floor."""
    if min_rows < 0:
        raise ValueError("min_rows must be non-negative")

    row_count = df.height
    if row_count < min_rows:
        raise GateError(f"row count {row_count} below floor {min_rows}")
    return row_count
