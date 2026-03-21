from dagster import RunFailureSensorContext, run_failure_sensor

from dagster_project.resources.slack import SlackResource


def _extract_root_cause(error) -> str:
    """Walk the cause chain to find the root error message and class."""
    if error is None:
        return "Unknown error"
    # Walk to the deepest cause
    while error.cause:
        error = error.cause
    cls = error.cls_name or "Error"
    return f"{cls}: {error.message}"


@run_failure_sensor
def slack_on_run_failure(
    context: RunFailureSensorContext, slack_resource: SlackResource
):
    """Send a Slack alert whenever any job run fails."""
    job_name = context.dagster_run.job_name
    run_id = context.dagster_run.run_id

    # Get step-level failure events for the actual error details
    step_failure_events = context.get_step_failure_events()

    failed_tasks = []
    if step_failure_events:
        for event in step_failure_events:
            step_key = event.step_key or "Unknown step"
            error = getattr(event.event_specific_data, "error", None)

            # Log full traceback for debugging in dagster logs
            if error:
                context.log.error(f"Full error for {step_key}:\n{error.to_string()}")

            root_cause = _extract_root_cause(error)
            failed_tasks.append((step_key, root_cause))
    else:
        error_message = "Unknown error"
        if context.failure_event and context.failure_event.message:
            error_message = context.failure_event.message
        failed_tasks.append(("Unknown", error_message))

    lines = [
        ":red_circle: *Job Failed*",
        f"*Job:* `{job_name}`",
    ]
    for step_key, error_msg in failed_tasks:
        lines.append(f"*Task:* `{step_key}`")
        lines.append(f"*Run ID:* `{run_id}`")
        lines.append(f"```{error_msg}```")

    message = "\n".join(lines)

    try:
        slack_resource.send_message(message=message)
    except Exception as e:
        context.log.error(f"Failed to send Slack failure alert: {e}")
