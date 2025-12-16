"""Tests using Dagster's materialize utility for end-to-end testing."""

import pytest
from unittest.mock import patch, MagicMock
from dagster import materialize

from dagster_project.assets.api_assets import api_users, users_in_postgres
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
        from contextlib import contextmanager

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

            # Create a real PostgresResource instance and replace get_connection with a mock
            mock_postgres = PostgresResource()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            # Create a proper context manager mock
            @contextmanager
            def mock_get_connection():
                yield mock_conn

            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_postgres.get_connection = mock_get_connection

            # Materialize both assets - ConfigurableResource instances can be passed directly
            result = materialize(
                [api_users, users_in_postgres],
                resources={"postgres": mock_postgres},
            )

            assert result.success
            mock_conn.commit.assert_called()
