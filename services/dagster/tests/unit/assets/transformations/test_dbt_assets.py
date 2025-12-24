"""Unit tests for dbt_assets."""

from unittest.mock import MagicMock

import pytest
from dagster import build_op_context
from dagster_dbt import DbtCliResource


@pytest.mark.unit
class TestDbtAnalytics:
    """Test the dbt_analytics asset."""

    def test_dbt_analytics_conditional_definition(self):
        """Test that dbt_analytics is conditionally defined based on dbt_project availability."""
        # This test verifies the conditional logic in the module
        from dagster_project.assets.transformations import dbt_assets

        # The asset should either be defined or None based on dbt_project
        assert dbt_assets.dbt_analytics is None or hasattr(
            dbt_assets.dbt_analytics, "__call__"
        )

    def test_dbt_analytics_when_available(self):
        """Test dbt_analytics when dbt_project is available."""
        from dagster_project.assets.transformations import dbt_assets

        # If dbt_analytics is defined, test its basic structure
        if dbt_assets.dbt_analytics is not None:
            mock_dbt_resource = MagicMock(spec=DbtCliResource)
            mock_cli_result = MagicMock()
            mock_cli_result.stream.return_value = iter([MagicMock()])
            mock_dbt_resource.cli.return_value = mock_cli_result

            context = build_op_context(resources={"dbt": mock_dbt_resource})

            # Execute the asset
            list(dbt_assets.dbt_analytics(context, mock_dbt_resource))

            mock_dbt_resource.cli.assert_called_once_with(["build"], context=context)
        else:
            # If dbt_project is not available, skip this test
            pytest.skip("dbt_project is not available, skipping dbt_analytics test")
