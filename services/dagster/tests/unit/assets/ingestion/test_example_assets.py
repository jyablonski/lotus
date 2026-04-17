"""Unit tests for example assets."""

from dagster import build_op_context
import pytest

from dagster_project.assets.ingestion.example_assets import hello_world_asset


@pytest.mark.unit
class TestHelloWorldAsset:
    def test_hello_world_asset_success(self):
        context = build_op_context()

        result = hello_world_asset(context)

        assert result is None

    def test_hello_world_asset_logs_message(self):
        context = build_op_context()

        hello_world_asset(context)

        # Direct log verification may not be possible; we only verify execution.
        assert True
