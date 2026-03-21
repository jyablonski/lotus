from contextlib import contextmanager

from dagster import ConfigurableResource, EnvVar
import polars as pl
import psycopg2


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


# connection only happens once an asset or op calls `get_connection` on the resource
postgres_conn = PostgresResource(
    host=EnvVar("DAGSTER_POSTGRES_HOST"),
    port=EnvVar.int("DAGSTER_POSTGRES_PORT"),
    user=EnvVar("DAGSTER_POSTGRES_USER"),
    password=EnvVar("DAGSTER_POSTGRES_PASSWORD"),
    database=EnvVar("DAGSTER_POSTGRES_DB"),
    schema_="source",
)
