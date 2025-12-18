"""Tests using Dagster's materialize utility for end-to-end testing."""

import pytest
from unittest.mock import patch, MagicMock
from dagster import materialize

from dagster_project.assets.ingestion.get_api_assets import api_users, users_in_postgres
from dagster_project.resources import PostgresResource


@pytest.mark.unit
class TestMaterialization:
    """Test asset materialization with mocked resources."""

    def test_materialize_api_users(self):
        """Test materializing api_users asset."""
        mock_users = [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser",
            }
        ]

        with patch("dagster_project.assets.api_assets.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_users
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = materialize([api_users])

            assert result.success
            assert result.asset_materializations_for_node("api_users") is not None

    def test_materialize_with_mocked_postgres(self):
        """Test materializing users_in_postgres with mocked database."""
        mock_users = [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser",
            }
        ]

        # Mock the API call
        with patch("dagster_project.assets.api_assets.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_users
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Patch psycopg2.connect at the module level since PostgresResource is frozen
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            # Patch psycopg2.connect to return our mock connection
            with patch(
                "dagster_project.resources.postgres.psycopg2.connect",
                return_value=mock_conn,
            ):
                # Create a real PostgresResource instance
                mock_postgres = PostgresResource()

                # Materialize both assets - ConfigurableResource instances can be passed directly
                result = materialize(
                    [api_users, users_in_postgres],
                    resources={"postgres": mock_postgres},
                )

                assert result.success
                mock_conn.commit.assert_called()
