"""Unit tests for dbt_assets."""

from unittest.mock import MagicMock

import pytest
from dagster import build_op_context
from dagster_dbt import DbtCliResource


@pytest.mark.unit
class TestDbtAssets:
    """Test the split dbt asset definitions (staging, core, analytics)."""

    def test_dbt_assets_conditional_definition(self):
        """Test that dbt assets are conditionally defined based on dbt_project availability."""
        from dagster_project.assets.transformations import dbt_assets

        for attr in ("dbt_silver_stg", "dbt_silver_core", "dbt_gold_analytics"):
            value = getattr(dbt_assets, attr)
            assert value is None or callable(value)

    @pytest.mark.parametrize(
        "asset_name", ["dbt_silver_stg", "dbt_silver_core", "dbt_gold_analytics"]
    )
    def test_dbt_asset_calls_build(self, asset_name):
        """Test each dbt asset invokes dbt build."""
        from dagster_project.assets.transformations import dbt_assets

        asset_fn = getattr(dbt_assets, asset_name)
        if asset_fn is None:
            pytest.skip(f"dbt_project not available, skipping {asset_name}")

        mock_dbt_resource = MagicMock(spec=DbtCliResource)
        mock_cli_result = MagicMock()
        mock_cli_result.stream.return_value = iter([MagicMock()])
        mock_dbt_resource.cli.return_value = mock_cli_result

        context = build_op_context(resources={"dbt": mock_dbt_resource})
        list(asset_fn(context, mock_dbt_resource))

        mock_dbt_resource.cli.assert_called_once_with(["build"], context=context)
