"""Tests for Slack notification hooks."""

from unittest.mock import MagicMock

from dagster import build_hook_context
import pytest

from dagster_project.ops.slack_hooks import create_slack_notification_hooks
from dagster_project.resources.slack import SlackResource


@pytest.mark.unit
class TestSlackNotificationHooks:
    """Test the create_slack_notification_hooks function."""

    def test_create_slack_notification_hooks_returns_set(self):
        """Test that create_slack_notification_hooks returns a set of hooks."""
        hooks = create_slack_notification_hooks(asset_name="test_asset")
        assert isinstance(hooks, set)
        assert len(hooks) == 2

    def test_create_slack_notification_hooks_default_messages(self):
        """Test that hooks are created with default messages."""
        hooks = create_slack_notification_hooks(asset_name="test_asset")
        hook_names = {hook.name for hook in hooks}
        assert "test_asset_success_hook" in hook_names
        assert "test_asset_failure_hook" in hook_names

    def test_create_slack_notification_hooks_custom_messages(self):
        """Test that hooks can be created with custom messages."""
        hooks = create_slack_notification_hooks(
            asset_name="test_asset",
            success_message="Custom success!",
            failure_message="Custom failure!",
        )
        assert len(hooks) == 2

    def test_create_slack_notification_hooks_custom_channel(self):
        """Test that hooks can be created with custom channel."""
        hooks = create_slack_notification_hooks(
            asset_name="test_asset",
            channel="#custom-channel",
        )
        assert len(hooks) == 2

    def test_success_hook_sends_message(self):
        """Test that success hook sends Slack message."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(asset_name="test_asset")
        success_hook = next(hook for hook in hooks if "success" in hook.name)

        # Build hook context with resources
        context = build_hook_context(resources={"slack_resource": mock_slack_resource})

        # Execute the hook
        success_hook.hook_fn(context)

        # Verify Slack message was sent
        mock_slack_resource.send_message.assert_called_once_with(
            message="✅ test_asset completed successfully!",
            channel=None,
        )
        context.log.info.assert_called_once()

    def test_success_hook_custom_message(self):
        """Test that success hook uses custom message."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(
            asset_name="test_asset",
            success_message="Custom success message!",
        )
        success_hook = next(hook for hook in hooks if "success" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})
        success_hook.hook_fn(context)

        mock_slack_resource.send_message.assert_called_once_with(
            message="Custom success message!",
            channel=None,
        )

    def test_success_hook_custom_channel(self):
        """Test that success hook uses custom channel."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(
            asset_name="test_asset",
            channel="#custom-channel",
        )
        success_hook = next(hook for hook in hooks if "success" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})
        success_hook.hook_fn(context)

        mock_slack_resource.send_message.assert_called_once_with(
            message="✅ test_asset completed successfully!",
            channel="#custom-channel",
        )

    def test_success_hook_handles_exception(self):
        """Test that success hook handles exceptions gracefully."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.side_effect = Exception("Slack API error")

        hooks = create_slack_notification_hooks(asset_name="test_asset")
        success_hook = next(hook for hook in hooks if "success" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})

        # Should not raise exception
        success_hook.hook_fn(context)

        context.log.error.assert_called_once()
        assert "Failed to send Slack success notification" in str(context.log.error.call_args)

    def test_failure_hook_sends_message(self):
        """Test that failure hook sends Slack message."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(asset_name="test_asset")
        failure_hook = next(hook for hook in hooks if "failure" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})
        # No exception attributes set by default
        failure_hook.hook_fn(context)

        mock_slack_resource.send_message.assert_called_once_with(
            message="❌ test_asset failed!",
            channel=None,
        )
        context.log.info.assert_called_once()

    def test_failure_hook_with_op_exception(self):
        """Test that failure hook includes op_exception details."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(asset_name="test_asset")
        failure_hook = next(hook for hook in hooks if "failure" in hook.name)

        context = build_hook_context(
            resources={"slack_resource": mock_slack_resource},
            op_exception=ValueError("Test error"),
        )
        failure_hook.hook_fn(context)

        call_args = mock_slack_resource.send_message.call_args
        assert call_args[1]["message"].startswith("❌ test_asset failed!")
        assert "Test error" in call_args[1]["message"]

    def test_failure_hook_with_step_exception(self):
        """Test that failure hook includes step_exception details when op_exception is None."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(asset_name="test_asset")
        failure_hook = next(hook for hook in hooks if "failure" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})
        # Set step_exception as attribute (build_hook_context doesn't support it directly)
        context.step_exception = RuntimeError("Step error")
        failure_hook.hook_fn(context)

        call_args = mock_slack_resource.send_message.call_args
        assert call_args[1]["message"].startswith("❌ test_asset failed!")
        assert "Step error" in call_args[1]["message"]

    def test_failure_hook_custom_message(self):
        """Test that failure hook uses custom message."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.return_value = {"ok": True}

        hooks = create_slack_notification_hooks(
            asset_name="test_asset",
            failure_message="Custom failure message!",
        )
        failure_hook = next(hook for hook in hooks if "failure" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})
        failure_hook.hook_fn(context)

        mock_slack_resource.send_message.assert_called_once_with(
            message="Custom failure message!",
            channel=None,
        )

    def test_failure_hook_handles_exception(self):
        """Test that failure hook handles exceptions gracefully."""
        mock_slack_resource = MagicMock(spec=SlackResource)
        mock_slack_resource.send_message.side_effect = Exception("Slack API error")

        hooks = create_slack_notification_hooks(asset_name="test_asset")
        failure_hook = next(hook for hook in hooks if "failure" in hook.name)

        context = build_hook_context(resources={"slack_resource": mock_slack_resource})

        # Should not raise exception
        failure_hook.hook_fn(context)

        context.log.error.assert_called_once()
        assert "Failed to send Slack failure notification" in str(context.log.error.call_args)

    def test_hooks_have_required_resource_keys(self):
        """Test that hooks require slack_resource."""
        hooks = create_slack_notification_hooks(asset_name="test_asset")
        for hook in hooks:
            assert "slack_resource" in hook.required_resource_keys
