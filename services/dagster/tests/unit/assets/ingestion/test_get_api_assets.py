"""Unit tests for API assets."""

from unittest.mock import MagicMock, patch

from dagster import ResourceDefinition, build_op_context
import pytest
import requests

from dagster_project.assets.ingestion.get_api_assets import (
    get_api_users,
    users_in_postgres,
)


@pytest.mark.unit
class TestApiUsers:
    def test_get_api_users_success(self):
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

            context = build_op_context()
            result = get_api_users(context)

            assert result == mock_users
            mock_get.assert_called_once_with(
                "https://jsonplaceholder.typicode.com/users"
            )

    def test_get_api_users_http_error(self):
        with patch(
            "dagster_project.assets.ingestion.get_api_assets.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
            mock_get.return_value = mock_response

            context = build_op_context()

            with pytest.raises(requests.HTTPError):
                get_api_users(context)


@pytest.mark.unit
class TestUsersInPostgres:
    def test_users_in_postgres_success(self, mock_postgres_resource, asset_context):
        mock_users = [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "username": "testuser",
            },
            {
                "id": 2,
                "name": "Another User",
                "email": "another@example.com",
                "username": "another",
            },
        ]

        # Wrap the mock in a ResourceDefinition so Dagster accepts it
        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})
        users_in_postgres(context, mock_users)

        mock_postgres_resource.get_connection.assert_called_once()
        mock_cursor = mock_postgres_resource.get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

        create_table_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "CREATE TABLE" in str(call)
        ]
        assert len(create_table_calls) > 0

        insert_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "INSERT INTO" in str(call)
        ]
        assert len(insert_calls) == len(mock_users)

        mock_conn = (
            mock_postgres_resource.get_connection.return_value.__enter__.return_value
        )
        mock_conn.commit.assert_called_once()

    def test_users_in_postgres_empty_list(self, mock_postgres_resource, asset_context):
        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})
        users_in_postgres(context, [])

        mock_postgres_resource.get_connection.assert_called_once()
        mock_conn = (
            mock_postgres_resource.get_connection.return_value.__enter__.return_value
        )
        mock_conn.commit.assert_called_once()
