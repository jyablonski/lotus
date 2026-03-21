"""SQL queries used by ingestion assets."""

CREATE_EXAMPLE_API_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS example_api_users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    username VARCHAR(255)
)
"""

UPSERT_EXAMPLE_API_USER = """
INSERT INTO example_api_users (id, name, email, username)
VALUES (%s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    username = EXCLUDED.username
"""
