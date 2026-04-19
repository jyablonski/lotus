from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any

from dagster import ConfigurableResource, EnvVar
import polars as pl
import psycopg2
from psycopg2.extras import Json, execute_values


def _quote_identifier(identifier: str) -> str:
    if not identifier or "\x00" in identifier:
        raise ValueError("Postgres identifiers must be non-empty strings")
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def _qualified_table_name(table_name: str, schema: str | None) -> str:
    if schema is not None:
        return f"{_quote_identifier(schema)}.{_quote_identifier(table_name)}"

    parts = table_name.split(".")
    return ".".join(_quote_identifier(part) for part in parts)


class PostgresResource(ConfigurableResource):
    host: str = "postgres"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"
    schema_: str = "source"  # trailing underscore because `schema` is reserved

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            options=f"-c search_path={self.schema_}",
        )
        try:
            yield conn
        finally:
            conn.close()

    def query_to_polars(self, query: str) -> pl.DataFrame:
        """Execute a SQL query and return the results as a Polars DataFrame."""
        with self.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return pl.DataFrame(rows, schema=columns, orient="row")

    def write_to_postgres(
        self,
        *,
        df: pl.DataFrame,
        table_name: str,
        conflict_columns: Sequence[str] | None = None,
        update_columns: Sequence[str] | None = None,
        json_columns: Sequence[str] | None = None,
        schema: str | None = None,
        cursor: Any | None = None,
        conn: Any | None = None,
        chunk_size: int = 1000,
    ) -> int:
        """Write a Polars DataFrame to Postgres with optional upsert semantics."""
        if df.is_empty():
            return 0

        if cursor is not None:
            return self._write_to_postgres_cursor(
                cursor,
                df,
                table_name,
                conflict_columns=conflict_columns,
                update_columns=update_columns,
                json_columns=json_columns,
                schema=schema,
                chunk_size=chunk_size,
            )

        if conn is not None:
            with conn.cursor() as cur:
                return self._write_to_postgres_cursor(
                    cur,
                    df,
                    table_name,
                    conflict_columns=conflict_columns,
                    update_columns=update_columns,
                    json_columns=json_columns,
                    schema=schema,
                    chunk_size=chunk_size,
                )

        with self.get_connection() as write_conn:
            with write_conn.cursor() as cur:
                row_count = self._write_to_postgres_cursor(
                    cur,
                    df,
                    table_name,
                    conflict_columns=conflict_columns,
                    update_columns=update_columns,
                    json_columns=json_columns,
                    schema=schema,
                    chunk_size=chunk_size,
                )
            write_conn.commit()
            return row_count

    def _write_to_postgres_cursor(
        self,
        cursor: Any,
        df: pl.DataFrame,
        table_name: str,
        *,
        conflict_columns: Sequence[str] | None,
        update_columns: Sequence[str] | None,
        json_columns: Sequence[str] | None,
        schema: str | None,
        chunk_size: int,
    ) -> int:
        columns = list(df.columns)
        if not columns:
            raise ValueError("Cannot write a DataFrame with no columns")

        conflict_columns = list(conflict_columns or [])
        json_columns = set(json_columns or [])
        if update_columns is None:
            update_columns = [
                column for column in columns if column not in conflict_columns
            ]
        update_columns = list(update_columns)

        unknown_columns = set(conflict_columns + update_columns) - set(columns)
        if unknown_columns:
            unknown = ", ".join(sorted(unknown_columns))
            raise ValueError(f"DataFrame is missing requested column(s): {unknown}")

        column_sql = ", ".join(_quote_identifier(column) for column in columns)
        query = (
            f"INSERT INTO {_qualified_table_name(table_name, schema)} "
            f"({column_sql}) VALUES %s"
        )
        if conflict_columns:
            conflict_sql = ", ".join(
                _quote_identifier(column) for column in conflict_columns
            )
            if update_columns:
                update_sql = ", ".join(
                    f"{_quote_identifier(column)} = EXCLUDED.{_quote_identifier(column)}"
                    for column in update_columns
                )
                query += f" ON CONFLICT ({conflict_sql}) DO UPDATE SET {update_sql}"
            else:
                query += f" ON CONFLICT ({conflict_sql}) DO NOTHING"

        values = [
            tuple(
                Json(row[column])
                if column in json_columns and row[column] is not None
                else row[column]
                for column in columns
            )
            for row in df.iter_rows(named=True)
        ]
        execute_values(cursor, query, values, page_size=chunk_size)
        return len(values)


# connection only happens once an asset or op calls `get_connection` on the resource
postgres_conn = PostgresResource(
    host=EnvVar("DAGSTER_POSTGRES_HOST"),
    port=EnvVar.int("DAGSTER_POSTGRES_PORT"),
    user=EnvVar("DAGSTER_POSTGRES_USER"),
    password=EnvVar("DAGSTER_POSTGRES_PASSWORD"),
    database=EnvVar("DAGSTER_POSTGRES_DB"),
    schema_="source",
)
