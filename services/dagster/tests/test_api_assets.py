"""Unit tests for API assets."""

from unittest.mock import MagicMock, patch

from dagster import ResourceDefinition, build_op_context
import pytest
import requests

from dagster_project.assets.ingestion.get_api_assets import api_users, users_in_postgres


@pytest.mark.unit
class TestApiUsers:
    """Test the api_users asset."""

    def test_api_users_success(self):
        """Test successful API fetch."""
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
            result = api_users(context)

            assert result == mock_users
            mock_get.assert_called_once_with(
                "https://jsonplaceholder.typicode.com/users"
            )

    def test_api_users_http_error(self):
        """Test handling of HTTP errors."""
        with patch(
            "dagster_project.assets.ingestion.get_api_assets.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
            mock_get.return_value = mock_response

            context = build_op_context()

            with pytest.raises(requests.HTTPError):
                api_users(context)


@pytest.mark.unit
class TestUsersInPostgres:
    """Test the users_in_postgres asset."""

    def test_users_in_postgres_success(self, mock_postgres_resource, asset_context):
        """Test successful storage of users in Postgres."""
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

        # Execute the asset with resources provided via context
        # Wrap the mock in a ResourceDefinition so Dagster accepts it
        def resource_fn(_context):
            return mock_postgres_resource

        postgres_resource_def = ResourceDefinition(resource_fn=resource_fn)
        context = build_op_context(resources={"postgres_conn": postgres_resource_def})
        users_in_postgres(context, mock_users)

        # Verify database interactions
        mock_postgres_resource.get_connection.assert_called_once()
        mock_cursor = mock_postgres_resource.get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

        # Check that CREATE TABLE was called
        create_table_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "CREATE TABLE" in str(call)
        ]
        assert len(create_table_calls) > 0

        # Check that INSERT statements were called for each user
        insert_calls = [
            call
            for call in mock_cursor.execute.call_args_list
            if "INSERT INTO" in str(call)
        ]
        assert len(insert_calls) == len(mock_users)

        # Verify commit was called
        mock_conn = (
            mock_postgres_resource.get_connection.return_value.__enter__.return_value
        )
        mock_conn.commit.assert_called_once()

    def test_users_in_postgres_empty_list(self, mock_postgres_resource, asset_context):
        """Test handling of empty user list."""

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
