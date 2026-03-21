from dagster import AssetExecutionContext, asset
import requests

from dagster_project.resources import PostgresResource
from dagster_project.sql.ingestion import (
    CREATE_EXAMPLE_API_USERS_TABLE,
    UPSERT_EXAMPLE_API_USER,
)


@asset(group_name="ingestion")
def get_api_users(context: AssetExecutionContext) -> list[dict]:
    """Fetch users from JSONPlaceholder API."""
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    response.raise_for_status()
    users = response.json()
    context.log.info(f"Fetched {len(users)} users from API")
    return users


@asset(group_name="ingestion")
def users_in_postgres(
    context: AssetExecutionContext,
    get_api_users: list[dict],
    postgres_conn: PostgresResource,
) -> None:
    """Store users in Postgres."""
    with postgres_conn.get_connection() as conn, conn.cursor() as cur:
        cur.execute(CREATE_EXAMPLE_API_USERS_TABLE)

        for user in get_api_users:
            cur.execute(
                UPSERT_EXAMPLE_API_USER,
                (user["id"], user["name"], user["email"], user["username"]),
            )

        conn.commit()

    context.log.info(f"Stored {len(get_api_users)} users in Postgres")
