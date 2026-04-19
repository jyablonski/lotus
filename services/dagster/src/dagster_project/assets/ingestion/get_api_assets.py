from dagster import AssetExecutionContext, asset
import polars as pl
import requests

from dagster_project.resources import PostgresResource


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
    users_df = pl.DataFrame(
        {
            "id": [user["id"] for user in get_api_users],
            "name": [user["name"] for user in get_api_users],
            "email": [user["email"] for user in get_api_users],
            "username": [user["username"] for user in get_api_users],
        }
    )
    postgres_conn.write_to_postgres(
        df=users_df,
        table_name="example_api_users",
        conflict_columns=["id"],
    )

    context.log.info(f"Stored {len(get_api_users)} users in Postgres")
