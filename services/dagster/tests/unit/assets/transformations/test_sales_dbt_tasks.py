import json
from unittest.mock import MagicMock

from dagster import AssetsDefinition, build_op_context
from dagster_dbt import DbtCliResource
import pytest

from dagster_project.defs.assets.transformations.sales_dbt_tasks import (
    SALES_DATA_DBT_ASSET_COMMANDS,
    SALES_DATA_DBT_STEP_COMMANDS,
    _manifest_has_tagged_asset,
    _run_dbt,
    build_dbt_step,
    sales_data_dbt_gold_build,
    sales_data_dbt_silver_build,
    sales_data_dbt_source_freshness,
    sales_data_dbt_source_tests,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("task_name", "expected_args"),
    [
        (
            "sales_data_dbt_source_freshness",
            ["source", "freshness", "--select", "source:sales_data"],
        ),
        (
            "sales_data_dbt_source_tests",
            ["test", "--select", "source:sales_data"],
        ),
    ],
)
def test_sales_dbt_step_commands_are_expected(task_name, expected_args):
    assert SALES_DATA_DBT_STEP_COMMANDS[task_name] == expected_args


@pytest.mark.unit
@pytest.mark.parametrize(
    ("task_name", "expected_args"),
    [
        (
            "sales_data_dbt_silver_build",
            ["build", "--select", "tag:silver,tag:sales_data"],
        ),
        (
            "sales_data_dbt_gold_build",
            ["build", "--select", "tag:gold,tag:sales_data"],
        ),
    ],
)
def test_sales_dbt_asset_commands_are_expected(task_name, expected_args):
    assert SALES_DATA_DBT_ASSET_COMMANDS[task_name] == expected_args


@pytest.mark.unit
def test_run_dbt_invokes_expected_command():
    mock_dbt_resource = MagicMock(spec=DbtCliResource)
    mock_cli_result = MagicMock()
    mock_cli_result.stream.return_value = iter([MagicMock()])
    mock_dbt_resource.cli.return_value = mock_cli_result
    context = build_op_context(resources={"dbt": mock_dbt_resource})

    _run_dbt(context, mock_dbt_resource, ["test", "--select", "source:sales_data"])

    mock_dbt_resource.cli.assert_called_once_with(
        ["test", "--select", "source:sales_data"],
        context=context,
    )


@pytest.mark.unit
def test_build_dbt_step_returns_named_asset_definition():
    step = build_dbt_step(
        name="example_dbt_step",
        args=["source", "freshness", "--select", "source:sales_data"],
        deps=[],
        description="dbt source freshness --select source:sales_data",
    )

    assert isinstance(step, AssetsDefinition)
    assert step.key.to_user_string() == "example_dbt_step"
    assert step.descriptions_by_key[step.key] == (
        "dbt source freshness --select source:sales_data"
    )


@pytest.mark.unit
def test_sales_dbt_assets_are_conditional_on_dbt_project():
    for asset_def in (
        sales_data_dbt_source_freshness,
        sales_data_dbt_source_tests,
        sales_data_dbt_silver_build,
        sales_data_dbt_gold_build,
    ):
        assert asset_def is None or callable(asset_def)


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
