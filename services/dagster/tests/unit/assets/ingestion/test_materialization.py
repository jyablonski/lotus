"""Tests using Dagster's materialize utility for end-to-end testing."""

from unittest.mock import MagicMock, patch

from dagster import materialize
import pytest

from dagster_project.assets.ingestion.get_api_assets import (
    get_api_users,
    users_in_postgres,
)
from dagster_project.resources import PostgresResource


@pytest.mark.unit
class TestMaterialization:
    def test_materialize_get_api_users(self):
        mock_users = [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser",
            }
        ]

        with patch(
            "dagster_project.assets.ingestion.get_api_assets.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_users
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = materialize([get_api_users])

            assert result.success
            assert result.asset_materializations_for_node("get_api_users") is not None

    def test_materialize_with_mocked_postgres(self):
        mock_users = [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser",
            }
        ]

        with patch(
            "dagster_project.assets.ingestion.get_api_assets.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_users
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Patch psycopg2.connect at the module level since PostgresResource is frozen
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            with (
                patch(
                    "dagster_project.resources.postgres.psycopg2.connect",
                    return_value=mock_conn,
                ),
                patch(
                    "dagster_project.resources.postgres.execute_values"
                ) as mock_execute_values,
            ):
                mock_postgres = PostgresResource()

                # ConfigurableResource instances can be passed directly to materialize.
                result = materialize(
                    [get_api_users, users_in_postgres],
                    resources={"postgres_conn": mock_postgres},
                )

                assert result.success
                mock_execute_values.assert_called_once()
                mock_conn.commit.assert_called()
