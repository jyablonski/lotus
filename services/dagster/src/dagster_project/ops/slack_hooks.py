from dagster import HookContext, HookDefinition, failure_hook, success_hook


def create_slack_notification_hooks(
    asset_name: str,
    success_message: str | None = None,
    failure_message: str | None = None,
    channel: str | None = None,
) -> set[HookDefinition]:
    """Create reusable Slack notification hooks for asset success/failure.

    Args:
        asset_name: Name of the asset to monitor (for display in messages)
        success_message: Custom success message (default: includes asset name and ✅)
        failure_message: Custom failure message (default: includes asset name and ❌)
        channel: Slack channel override (uses default_channel from resource if None)

    Returns:
        Set of HookDefinition objects (success and failure hooks)

    Example:
        ```python
        hooks = create_slack_notification_hooks(
            asset_name="unload_journals_to_s3",
            success_message="Journal entries unloaded successfully!",
        )
        unload_job = define_asset_job(..., hooks=hooks)
        ```
    """
    if success_message is None:
        success_message = f"✅ {asset_name} completed successfully!"

    if failure_message is None:
        failure_message = f"❌ {asset_name} failed!"

    # Capture variables for closure
    success_msg = success_message
    failure_msg = failure_message
    slack_channel = channel

    @success_hook(
        required_resource_keys={"slack_resource"}, name=f"{asset_name}_success_hook"
    )
    def success_hook_fn(context: HookContext):
        """Hook that sends Slack notification on asset success."""
        slack = context.resources.slack_resource
        try:
            slack.send_message(
                message=success_msg,
                channel=slack_channel,
            )
            context.log.info(f"Slack success notification sent for {asset_name}")
        except Exception as e:
            context.log.error(f"Failed to send Slack success notification: {e}")

    @failure_hook(
        required_resource_keys={"slack_resource"}, name=f"{asset_name}_failure_hook"
    )
    def failure_hook_fn(context: HookContext):
        """Hook that sends Slack notification on asset failure."""
        slack = context.resources.slack_resource
        try:
            # Include error details in failure message
            error_details = ""
            if hasattr(context, "op_exception") and context.op_exception:
                error_details = f"\nError: {context.op_exception!s}"
            elif hasattr(context, "step_exception") and context.step_exception:
                error_details = f"\nError: {context.step_exception!s}"

            full_message = failure_msg + error_details
            slack.send_message(
                message=full_message,
                channel=slack_channel,
            )
            context.log.info(f"Slack failure notification sent for {asset_name}")
        except Exception as e:
            context.log.error(f"Failed to send Slack failure notification: {e}")

    # The decorators already return HookDefinition objects, so return them directly
    return {success_hook_fn, failure_hook_fn}
