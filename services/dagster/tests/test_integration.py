"""Integration tests for Dagster assets and jobs.

These tests require the Docker Compose postgres service to be running.
Start it with: docker-compose -f ../../docker/docker-compose-local.yaml up -d postgres

Run with: pytest -m integration
"""

from dagster import build_asset_context
import pytest

from dagster_project.assets.ingestion.get_api_assets import api_users, users_in_postgres


@pytest.mark.integration
@pytest.mark.slow
class TestIntegration:
    """Integration tests that require external services."""

    def test_api_users_integration(self):
        """Test api_users asset with real API call."""
        context = build_asset_context()
        result = api_users(context)

        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "name" in result[0]
        assert "email" in result[0]

    def test_users_in_postgres_integration(self, postgres_resource_with_cleanup):
        """Test users_in_postgres asset with real Docker Postgres database.

        Uses the postgres service from docker-compose-local.yaml.
        No cleanup is performed - test data persists after the test.
        """
        # Create test users
        test_users = [
            {
                "id": 999,
                "name": "Integration Test User",
                "email": "integration@test.com",
                "username": "integration_test",
            }
        ]

        context = build_asset_context()

        # Execute the asset
        users_in_postgres(context, test_users, postgres_resource_with_cleanup)

        # Verify data was stored
        # Note: search_path is set in PostgresResource, so table is in the test schema
        with postgres_resource_with_cleanup.get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM example_api_users WHERE id = %s", (999,))
            result = cur.fetchone()
            assert result is not None
            assert result[1] == "Integration Test User"
            assert result[2] == "integration@test.com"
            assert result[3] == "integration_test"
