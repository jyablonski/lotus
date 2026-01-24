from contextlib import contextmanager

from dagster import ConfigurableResource, EnvVar
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
    host=EnvVar("DAGSTER_POSTGRES_HOST"),
    port=EnvVar.int("DAGSTER_POSTGRES_PORT"),
    user=EnvVar("DAGSTER_POSTGRES_USER"),
    password=EnvVar("DAGSTER_POSTGRES_PASSWORD"),
    database=EnvVar("DAGSTER_POSTGRES_DB"),
    schema_="source",
)
