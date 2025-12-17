import requests
from dagster import asset, AssetExecutionContext

from dagster_project.resources import PostgresResource


@asset
def api_users(context: AssetExecutionContext) -> list[dict]:
    """Fetch users from JSONPlaceholder API."""
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    response.raise_for_status()
    users = response.json()
    context.log.info(f"Fetched {len(users)} users from API")
    return users


@asset
def users_in_postgres(
    context: AssetExecutionContext,
    api_users: list[dict],
    postgres: PostgresResource,
) -> None:
    """Store users in Postgres."""
    with postgres.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS example_api_users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    username VARCHAR(255)
                )
            """)

            for user in api_users:
                cur.execute(
                    """
                    INSERT INTO example_api_users (id, name, email, username)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        username = EXCLUDED.username
                    """,
                    (user["id"], user["name"], user["email"], user["username"]),
                )

            conn.commit()

    context.log.info(f"Stored {len(api_users)} users in Postgres")
