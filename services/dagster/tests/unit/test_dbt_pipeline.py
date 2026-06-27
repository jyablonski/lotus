import json
from unittest.mock import MagicMock

from dagster import AssetsDefinition, build_op_context
from dagster_dbt import DbtCliResource
import pytest

from dagster_project.dbt_pipeline import (
    _layer_build_args,
    _manifest_has_tagged_asset,
    _run_dbt,
    _source_freshness_args,
    _source_tests_args,
    build_dbt_step,
)


@pytest.mark.unit
@pytest.mark.parametrize("data_source", ["sales_data", "game_bets"])
def test_source_step_args_are_parameterized_by_data_source(data_source):
    assert _source_freshness_args(data_source) == [
        "source",
        "freshness",
        "--select",
        f"source:{data_source}",
    ]
    assert _source_tests_args(data_source) == [
        "test",
        "--select",
        f"source:{data_source}",
    ]


@pytest.mark.unit
@pytest.mark.parametrize("data_source", ["sales_data", "game_bets"])
@pytest.mark.parametrize("layer_tag", ["silver", "gold"])
def test_layer_build_args_are_parameterized(layer_tag, data_source):
    assert _layer_build_args(layer_tag, data_source) == [
        "build",
        "--select",
        f"tag:{layer_tag},tag:{data_source}",
    ]


@pytest.mark.unit
def test_run_dbt_invokes_expected_command():
    mock_dbt_resource = MagicMock(spec=DbtCliResource)
    mock_cli_result = MagicMock()
    mock_dbt_resource.cli.return_value = mock_cli_result
    context = build_op_context(resources={"dbt": mock_dbt_resource})

    _run_dbt(context, mock_dbt_resource, ["test", "--select", "source:revenue"])

    # Plain ops run the command via .wait() (not .stream(), which needs a
    # @dbt_assets manifest context).
    mock_dbt_resource.cli.assert_called_once_with(
        ["test", "--select", "source:revenue"]
    )
    mock_cli_result.wait.assert_called_once_with()


@pytest.mark.unit
def test_build_dbt_step_returns_named_asset_definition():
    step = build_dbt_step(
        name="example_dbt_step",
        args=["source", "freshness", "--select", "source:sales_data"],
        deps=[],
        description="dbt source freshness --select source:sales_data",
        group_name="transformations",
    )

    assert isinstance(step, AssetsDefinition)
    assert step.key.to_user_string() == "example_dbt_step"
    assert step.descriptions_by_key[step.key] == (
        "dbt source freshness --select source:sales_data"
    )


@pytest.mark.unit
def test_manifest_has_tagged_asset(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "nodes": {
                    "model.project.stg_sales_data": {
                        "resource_type": "model",
                        "tags": ["silver", "sales_data"],
                    },
                    "test.project.not_an_asset": {
                        "resource_type": "test",
                        "tags": ["silver", "sales_data"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    assert _manifest_has_tagged_asset(manifest_path, {"silver", "sales_data"})
    assert not _manifest_has_tagged_asset(manifest_path, {"gold", "sales_data"})
