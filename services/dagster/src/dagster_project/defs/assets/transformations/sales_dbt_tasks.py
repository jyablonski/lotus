from collections.abc import Mapping, Sequence
import json
from typing import Any

from dagster import AssetExecutionContext, AssetSpec, AssetsDefinition, asset
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from dagster_project.dbt_config import dbt_project
from dagster_project.defs.assets.ingestion.get_sales_data import sales_data_bronze

SALES_DATA_SOURCE_NAME = "sales_data"
SALES_DATA_TAG = "sales_data"
SALES_DATA_DBT_STEP_COMMANDS = {
    "sales_data_dbt_source_freshness": [
        "source",
        "freshness",
        "--select",
        f"source:{SALES_DATA_SOURCE_NAME}",
    ],
    "sales_data_dbt_source_tests": [
        "test",
        "--select",
        f"source:{SALES_DATA_SOURCE_NAME}",
    ],
}
SALES_DATA_DBT_ASSET_COMMANDS = {
    "sales_data_dbt_silver_build": [
        "build",
        "--select",
        f"tag:silver,tag:{SALES_DATA_TAG}",
    ],
    "sales_data_dbt_gold_build": [
        "build",
        "--select",
        f"tag:gold,tag:{SALES_DATA_TAG}",
    ],
}
DBT_ASSET_RESOURCE_TYPES = {"model", "seed", "snapshot"}


def _run_dbt(
    context: AssetExecutionContext,
    dbt: DbtCliResource,
    args: Sequence[str],
) -> None:
    context.log.info(f"Running dbt command: dbt {' '.join(args)}")
    for _event in dbt.cli(list(args), context=context).stream():
        pass


def build_dbt_step(
    name: str,
    args: Sequence[str],
    deps: Sequence[Any],
    description: str,
) -> AssetsDefinition:
    @asset(
        name=name,
        group_name="transformations",
        deps=list(deps),
        description=description,
    )
    def _step(context: AssetExecutionContext, dbt: DbtCliResource) -> None:
        _run_dbt(context, dbt, args)

    return _step


class SalesDataDbtTranslator(DagsterDbtTranslator):
    def get_asset_spec(
        self,
        manifest: Mapping[str, Any],
        unique_id: str,
        project,
    ) -> AssetSpec:
        spec = super().get_asset_spec(manifest, unique_id, project)
        resource_props = self.get_resource_props(manifest, unique_id)
        resource_tags = set(resource_props.get("tags", []))

        if {"silver", SALES_DATA_TAG}.issubset(resource_tags):
            return spec.merge_attributes(deps=[sales_data_dbt_source_tests])

        return spec


def _manifest_has_tagged_asset(manifest_path: Any, required_tags: set[str]) -> bool:
    with open(manifest_path) as manifest_file:
        manifest = json.load(manifest_file)

    for node in manifest.get("nodes", {}).values():
        if node.get("resource_type") not in DBT_ASSET_RESOURCE_TYPES:
            continue

        if required_tags.issubset(set(node.get("tags", []))):
            return True

    return False


if dbt_project is not None:
    manifest_path = dbt_project.manifest_path
    has_sales_silver_assets = _manifest_has_tagged_asset(
        manifest_path,
        {"silver", SALES_DATA_TAG},
    )
    has_sales_gold_assets = _manifest_has_tagged_asset(
        manifest_path,
        {"gold", SALES_DATA_TAG},
    )

    sales_data_dbt_source_freshness = build_dbt_step(
        name="sales_data_dbt_source_freshness",
        args=SALES_DATA_DBT_STEP_COMMANDS["sales_data_dbt_source_freshness"],
        deps=[sales_data_bronze],
        description="dbt source freshness --select source:sales_data",
    )
    sales_data_dbt_source_tests = build_dbt_step(
        name="sales_data_dbt_source_tests",
        args=SALES_DATA_DBT_STEP_COMMANDS["sales_data_dbt_source_tests"],
        deps=[sales_data_dbt_source_freshness],
        description="dbt test --select source:sales_data",
    )

    if has_sales_silver_assets:

        @dbt_assets(
            manifest=manifest_path,
            select=f"tag:silver,tag:{SALES_DATA_TAG}",
            name="sales_data_dbt_silver_build",
            dagster_dbt_translator=SalesDataDbtTranslator(),
        )
        def sales_data_dbt_silver_build(
            context: AssetExecutionContext,
            dbt: DbtCliResource,
        ):
            yield from dbt.cli(
                SALES_DATA_DBT_ASSET_COMMANDS["sales_data_dbt_silver_build"],
                context=context,
            ).stream()

    else:
        sales_data_dbt_silver_build = None

    if has_sales_gold_assets:

        @dbt_assets(
            manifest=manifest_path,
            select=f"tag:gold,tag:{SALES_DATA_TAG}",
            name="sales_data_dbt_gold_build",
        )
        def sales_data_dbt_gold_build(
            context: AssetExecutionContext,
            dbt: DbtCliResource,
        ):
            yield from dbt.cli(
                SALES_DATA_DBT_ASSET_COMMANDS["sales_data_dbt_gold_build"],
                context=context,
            ).stream()

    else:
        sales_data_dbt_gold_build = None

else:
    sales_data_dbt_source_freshness = None
    sales_data_dbt_source_tests = None
    sales_data_dbt_silver_build = None
    sales_data_dbt_gold_build = None
