from dagster import ConfigurableResource, EnvVar
import requests


class SlackResource(ConfigurableResource):
    """Resource for sending messages to Slack via webhook or bot token."""

    webhook_url: str = ""
    bot_token: str = ""
    default_channel: str = ""

    def send_message(
        self,
        message: str,
        channel: str | None = None,
        username: str | None = None,
        icon_emoji: str | None = None,
    ) -> dict:
        """Send a message to Slack.

        Args:
            message: The message text to send
            channel: Slack channel ID or name (overrides default_channel if set)
            username: Display name for the bot (webhook only)
            icon_emoji: Emoji icon for the bot (webhook only, e.g., ":robot_face:")

        Returns:
            Response dictionary from Slack API

        Raises:
            ValueError: If neither webhook_url nor bot_token is configured
            requests.RequestException: If the request fails
        """
        channel = channel or self.default_channel

        if self.webhook_url:
            return self._send_via_webhook(message, channel, username, icon_emoji)
        elif self.bot_token:
            return self._send_via_bot_token(message, channel)
        else:
            raise ValueError("Either webhook_url or bot_token must be configured")

    def _send_via_webhook(
        self,
        message: str,
        channel: str | None,
        username: str | None,
        icon_emoji: str | None,
    ) -> dict:
        """Send message via Slack webhook URL."""
        payload = {"text": message}
        if channel:
            payload["channel"] = channel
        if username:
            payload["username"] = username
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        response = requests.post(self.webhook_url, json=payload, timeout=10)
        response.raise_for_status()

        # Slack webhooks return "ok" as plain text, not JSON
        # Return a dict with the status for consistency
        if response.text.strip() == "ok":
            return {"ok": True, "text": response.text}
        # Try to parse as JSON if it's not "ok"
        try:
            return response.json()
        except ValueError:
            # If not JSON, return the text response
            return {"ok": True, "text": response.text}

    def _send_via_bot_token(self, message: str, channel: str | None) -> dict:
        """Send message via Slack Bot Token API."""
        if not channel:
            raise ValueError("channel is required when using bot_token")

        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json",
        }
        payload = {"channel": channel, "text": message}

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if not result.get("ok"):
            raise ValueError(f"Slack API error: {result.get('error', 'Unknown error')}")

        return result


# Create default Slack resource instance
slack_resource = SlackResource(
    webhook_url=EnvVar("SLACK_WEBHOOK_URL"),
    bot_token=EnvVar("SLACK_BOT_TOKEN"),
    default_channel=EnvVar("SLACK_DEFAULT_CHANNEL"),
)
