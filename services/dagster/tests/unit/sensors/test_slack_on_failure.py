"""Unit tests for Slack failure sensor."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from dagster_project.sensors.slack_on_failure import (
    _extract_root_cause,
    slack_on_run_failure,
)


def _build_serializable_error(
    message: str,
    cls_name: str = "DagsterError",
    cause=None,
    traceback_text: str = "traceback",
):
    return SimpleNamespace(
        message=message,
        cls_name=cls_name,
        cause=cause,
        to_string=lambda: traceback_text,
    )


@pytest.mark.unit
class TestSlackOnFailureSensor:
    """Test failure sensor messaging and error extraction."""

    def test_extract_root_cause_walks_cause_chain(self):
        root_error = _build_serializable_error("db timed out", cls_name="DatabaseError")
        wrapped_error = _build_serializable_error(
            "job failed",
            cls_name="DagsterExecutionStepExecutionError",
            cause=root_error,
        )

        assert _extract_root_cause(wrapped_error) == "DatabaseError: db timed out"
        assert _extract_root_cause(None) == "Unknown error"

    def test_sensor_sends_step_failure_details(self):
        root_error = _build_serializable_error("db timed out", cls_name="DatabaseError")
        wrapped_error = _build_serializable_error(
            "job failed",
            cls_name="DagsterExecutionStepExecutionError",
            cause=root_error,
            traceback_text="full traceback",
        )
        failure_event = SimpleNamespace(
            step_key="persist_users",
            event_specific_data=SimpleNamespace(error=wrapped_error),
        )
        context = MagicMock()
        context.dagster_run = SimpleNamespace(
            job_name="sync_users_job",
            run_id="run-123",
        )
        context.get_step_failure_events.return_value = [failure_event]
        context.failure_event = None
        slack_resource = MagicMock()

        slack_on_run_failure._run_status_sensor_fn(context, slack_resource)

        sent_message = slack_resource.send_message.call_args.kwargs["message"]
        assert "*Job:* `sync_users_job`" in sent_message
        assert "*Task:* `persist_users`" in sent_message
        assert "*Run ID:* `run-123`" in sent_message
        assert "```DatabaseError: db timed out```" in sent_message
        context.log.error.assert_called_once_with(
            "Full error for persist_users:\nfull traceback"
        )

    def test_sensor_falls_back_to_failure_event_message(self):
        context = MagicMock()
        context.dagster_run = SimpleNamespace(
            job_name="sync_users_job",
            run_id="run-456",
        )
        context.get_step_failure_events.return_value = []
        context.failure_event = SimpleNamespace(
            message="Run failed before steps started"
        )
        slack_resource = MagicMock()

        slack_on_run_failure._run_status_sensor_fn(context, slack_resource)

        sent_message = slack_resource.send_message.call_args.kwargs["message"]
        assert "*Task:* `Unknown`" in sent_message
        assert "```Run failed before steps started```" in sent_message

    def test_sensor_logs_when_slack_send_fails(self):
        context = MagicMock()
        context.dagster_run = SimpleNamespace(
            job_name="sync_users_job", run_id="run-789"
        )
        context.get_step_failure_events.return_value = []
        context.failure_event = SimpleNamespace(message="boom")
        slack_resource = MagicMock()
        slack_resource.send_message.side_effect = RuntimeError("slack unavailable")

        slack_on_run_failure._run_status_sensor_fn(context, slack_resource)

        context.log.error.assert_called_once_with(
            "Failed to send Slack failure alert: slack unavailable"
        )
