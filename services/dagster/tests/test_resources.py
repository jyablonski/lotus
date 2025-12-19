"""Tests for Dagster resources."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from dagster_project.resources import PostgresResource
from dagster_project.resources.slack import SlackResource


@pytest.mark.unit
class TestPostgresResource:
    """Test the PostgresResource."""

    def test_postgres_resource_initialization(self):
        """Test resource initialization with defaults."""
        resource = PostgresResource()
        assert resource.host == "postgres"
        assert resource.port == 5432
        assert resource.user == "postgres"
        assert resource.password == "postgres"
        assert resource.database == "postgres"
        assert resource.schema_ == "source"

    def test_postgres_resource_custom_config(self):
        """Test resource initialization with custom config."""
        resource = PostgresResource(
            host="custom_host",
            port=5433,
            user="custom_user",
            password="custom_pass",
            database="custom_db",
            schema_="custom_schema",
        )
        assert resource.host == "custom_host"
        assert resource.port == 5433
        assert resource.user == "custom_user"
        assert resource.password == "custom_pass"
        assert resource.database == "custom_db"
        assert resource.schema_ == "custom_schema"

    @patch("dagster_project.resources.postgres.psycopg2.connect")
    def test_get_connection(self, mock_connect):
        """Test connection context manager."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        resource = PostgresResource()
        with resource.get_connection() as conn:
            assert conn == mock_conn

        mock_connect.assert_called_once_with(
            host="postgres",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres",
            options="-c search_path=source",
        )
        mock_conn.close.assert_called_once()


@pytest.mark.unit
class TestSlackResource:
    """Test the SlackResource."""

    def test_slack_resource_initialization_defaults(self):
        """Test resource initialization with defaults."""
        resource = SlackResource()
        assert resource.webhook_url == ""
        assert resource.bot_token == ""
        assert resource.default_channel == ""

    def test_slack_resource_custom_config(self):
        """Test resource initialization with custom config."""
        resource = SlackResource(
            webhook_url="https://hooks.slack.com/test",
            bot_token="xoxb-test-token",
            default_channel="#general",
        )
        assert resource.webhook_url == "https://hooks.slack.com/test"
        assert resource.bot_token == "xoxb-test-token"
        assert resource.default_channel == "#general"

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_success(self, mock_post):
        """Test sending message via webhook successfully."""
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(webhook_url="https://hooks.slack.com/test")
        result = resource.send_message("Test message")

        assert result == {"ok": True, "text": "ok"}
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/test",
            json={"text": "Test message"},
            timeout=10,
        )

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_with_channel(self, mock_post):
        """Test sending message via webhook with channel override."""
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(webhook_url="https://hooks.slack.com/test")
        result = resource.send_message("Test message", channel="#test-channel")

        assert result == {"ok": True, "text": "ok"}
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/test",
            json={"text": "Test message", "channel": "#test-channel"},
            timeout=10,
        )

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_with_username_and_emoji(self, mock_post):
        """Test sending message via webhook with username and emoji."""
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(webhook_url="https://hooks.slack.com/test")
        result = resource.send_message(
            "Test message",
            username="TestBot",
            icon_emoji=":robot_face:",
        )

        assert result == {"ok": True, "text": "ok"}
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/test",
            json={
                "text": "Test message",
                "username": "TestBot",
                "icon_emoji": ":robot_face:",
            },
            timeout=10,
        )

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_uses_default_channel(self, mock_post):
        """Test sending message via webhook uses default_channel when channel not provided."""
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(
            webhook_url="https://hooks.slack.com/test",
            default_channel="#default",
        )
        result = resource.send_message("Test message")

        assert result == {"ok": True, "text": "ok"}
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/test",
            json={"text": "Test message", "channel": "#default"},
            timeout=10,
        )

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_json_response(self, mock_post):
        """Test sending message via webhook with JSON response."""
        mock_response = MagicMock()
        mock_response.text = '{"ok": true, "message": "sent"}'
        mock_response.json.return_value = {"ok": True, "message": "sent"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(webhook_url="https://hooks.slack.com/test")
        result = resource.send_message("Test message")

        assert result == {"ok": True, "message": "sent"}

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_non_json_response(self, mock_post):
        """Test sending message via webhook with non-JSON, non-ok response."""
        mock_response = MagicMock()
        mock_response.text = "some other response"
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(webhook_url="https://hooks.slack.com/test")
        result = resource.send_message("Test message")

        assert result == {"ok": True, "text": "some other response"}

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_webhook_http_error(self, mock_post):
        """Test sending message via webhook raises HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_post.return_value = mock_response

        resource = SlackResource(webhook_url="https://hooks.slack.com/test")

        with pytest.raises(requests.HTTPError):
            resource.send_message("Test message")

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_bot_token_success(self, mock_post):
        """Test sending message via bot token successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(bot_token="xoxb-test-token")
        result = resource.send_message("Test message", channel="#test-channel")

        assert result == {"ok": True, "ts": "1234567890.123456"}
        mock_post.assert_called_once_with(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": "Bearer xoxb-test-token",
                "Content-Type": "application/json",
            },
            json={"channel": "#test-channel", "text": "Test message"},
            timeout=10,
        )

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_bot_token_uses_default_channel(self, mock_post):
        """Test sending message via bot token uses default_channel when channel not provided."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(
            bot_token="xoxb-test-token",
            default_channel="#default",
        )
        result = resource.send_message("Test message")

        assert result == {"ok": True}
        mock_post.assert_called_once_with(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": "Bearer xoxb-test-token",
                "Content-Type": "application/json",
            },
            json={"channel": "#default", "text": "Test message"},
            timeout=10,
        )

    @patch("dagster_project.resources.slack.requests.post")
    def test_send_message_via_bot_token_api_error(self, mock_post):
        """Test sending message via bot token raises error when API returns error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        resource = SlackResource(bot_token="xoxb-test-token")

        with pytest.raises(ValueError, match="Slack API error: channel_not_found"):
            resource.send_message("Test message", channel="#test-channel")

    def test_send_message_via_bot_token_no_channel(self):
        """Test sending message via bot token raises error when channel is missing."""
        resource = SlackResource(bot_token="xoxb-test-token")

        with pytest.raises(ValueError, match="channel is required when using bot_token"):
            resource.send_message("Test message")

    def test_send_message_no_config(self):
        """Test sending message raises error when neither webhook_url nor bot_token is configured."""
        resource = SlackResource()

        with pytest.raises(ValueError, match="Either webhook_url or bot_token must be configured"):
            resource.send_message("Test message")

    def test_send_message_webhook_takes_precedence(self):
        """Test that webhook_url takes precedence over bot_token when both are set."""
        resource = SlackResource(
            webhook_url="https://hooks.slack.com/test",
            bot_token="xoxb-test-token",
        )

        # Should use webhook, not bot token
        with patch.object(resource, "_send_via_webhook") as mock_webhook:
            mock_webhook.return_value = {"ok": True}
            resource.send_message("Test message")
            mock_webhook.assert_called_once()
