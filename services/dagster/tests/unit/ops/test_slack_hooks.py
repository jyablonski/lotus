"""Unit tests for Slack notification hooks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from dagster_project.ops.slack_hooks import create_slack_notification_hooks


def _build_hook_context(slack_resource: MagicMock, **extra_attrs) -> MagicMock:
    context = MagicMock()
    context.resources = SimpleNamespace(slack_resource=slack_resource)
    for attr_name, attr_value in extra_attrs.items():
        setattr(context, attr_name, attr_value)
    return context


@pytest.mark.unit
class TestSlackHooks:
    """Test Slack hook generation and behavior."""

    def test_create_slack_notification_hooks_uses_defaults(self):
        hooks = create_slack_notification_hooks(asset_name="sync_asset")

        hook_names = {hook.name for hook in hooks}
        assert hook_names == {"sync_asset_success_hook", "sync_asset_failure_hook"}
        assert all(hook.required_resource_keys == {"slack_resource"} for hook in hooks)

    def test_success_hook_sends_custom_message(self):
        hooks = create_slack_notification_hooks(
            asset_name="sync_asset",
            success_message="Done syncing",
            channel="#alerts",
        )
        success_hook = next(
            hook for hook in hooks if hook.name.endswith("success_hook")
        )
        slack_resource = MagicMock()
        context = _build_hook_context(slack_resource)

        success_hook.decorated_fn(context)

        slack_resource.send_message.assert_called_once_with(
            message="Done syncing",
            channel="#alerts",
        )
        context.log.info.assert_called_once()
        context.log.error.assert_not_called()

    def test_failure_hook_includes_error_details(self):
        hooks = create_slack_notification_hooks(
            asset_name="sync_asset",
            failure_message="Sync failed",
        )
        failure_hook = next(
            hook for hook in hooks if hook.name.endswith("failure_hook")
        )
        slack_resource = MagicMock()
        context = _build_hook_context(
            slack_resource,
            op_exception=RuntimeError("boom"),
            step_exception=None,
        )

        failure_hook.decorated_fn(context)

        slack_resource.send_message.assert_called_once_with(
            message="Sync failed\nError: boom",
            channel=None,
        )
        context.log.info.assert_called_once()

    def test_failure_hook_logs_when_slack_send_fails(self):
        hooks = create_slack_notification_hooks(asset_name="sync_asset")
        failure_hook = next(
            hook for hook in hooks if hook.name.endswith("failure_hook")
        )
        slack_resource = MagicMock()
        slack_resource.send_message.side_effect = RuntimeError("slack unavailable")
        context = _build_hook_context(
            slack_resource,
            op_exception=None,
            step_exception=RuntimeError("step failed"),
        )

        failure_hook.decorated_fn(context)

        context.log.error.assert_called_once()
