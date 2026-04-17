"""Integration tests for Dagster assets and jobs.

Postgres-backed integration tests use a testcontainer-managed database.
Run with: pytest -m integration
"""

from dagster import build_asset_context
import pytest
import requests

from dagster_project.assets.ingestion.get_api_assets import (
    get_api_users,
    users_in_postgres,
)


@pytest.mark.integration
@pytest.mark.slow
class TestIntegration:
    def test_get_api_users_integration(self):
        context = build_asset_context()
        try:
            result = get_api_users(context)
        except requests.RequestException as exc:
            pytest.skip(f"External API unavailable for integration test: {exc}")

        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "name" in result[0]
        assert "email" in result[0]

    def test_users_in_postgres_integration(self, postgres_resource_with_cleanup):
        test_users = [
            {
                "id": 999,
                "name": "Integration Test User",
                "email": "integration@test.com",
                "username": "integration_test",
            }
        ]

        context = build_asset_context()

        users_in_postgres(context, test_users, postgres_resource_with_cleanup)

        # search_path is set in PostgresResource, so table is in the test schema
        with (
            postgres_resource_with_cleanup.get_connection() as conn,
            conn.cursor() as cur,
        ):
            cur.execute("SELECT * FROM example_api_users WHERE id = %s", (999,))
            result = cur.fetchone()
            assert result is not None
            assert result[1] == "Integration Test User"
            assert result[2] == "integration@test.com"
            assert result[3] == "integration_test"
