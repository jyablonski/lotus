import os

from dagster import ConfigurableResource
from contextlib import contextmanager
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


# connection only happens once an asset or op calls `get_connection` on the resource
postgres_conn = PostgresResource(
    host=os.getenv("DAGSTER_POSTGRES_HOST", "postgres"),
    port=int(os.getenv("DAGSTER_POSTGRES_PORT", "5432")),
    user=os.getenv("DAGSTER_POSTGRES_USER", "postgres"),
    password=os.getenv("DAGSTER_POSTGRES_PASSWORD", "postgres"),
    database=os.getenv("DAGSTER_POSTGRES_DB", "postgres"),
    schema_="source",
)
