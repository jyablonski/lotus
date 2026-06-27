from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_project.dbt_config import dbt_project
from dagster_project.dbt_pipeline import source_pipeline_exclude

# Split dbt assets into one definition per layer so Dagster runs each as a
# separate op/step, giving visibility in the Gantt chart.
# Only defined when dbt_project is available (test resilience).
if dbt_project is not None:
    manifest_path = dbt_project.manifest_path

    # Models owned by a per-source pipeline are excluded here so each dbt model
    # belongs to exactly one @dbt_assets definition (no duplicate asset keys).
    _exclude = source_pipeline_exclude()

    def _dbt_layer_assets(*, name: str, tag: str):
        @dbt_assets(
            manifest=manifest_path,
            select=f"tag:{tag}",
            exclude=_exclude,
            name=name,
        )
        def _assets(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        return _assets

    dbt_silver_stg = _dbt_layer_assets(name="dbt_silver_stg", tag="staging")
    dbt_silver_core = _dbt_layer_assets(name="dbt_silver_core", tag="core")
    dbt_gold_analytics = _dbt_layer_assets(
        name="dbt_gold_analytics",
        tag="analytics",
    )

else:
    dbt_silver_stg = None
    dbt_silver_core = None
    dbt_gold_analytics = None
