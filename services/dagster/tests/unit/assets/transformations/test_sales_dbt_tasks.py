import pytest

from dagster_project.dbt_pipeline import DbtSourcePipeline
from dagster_project.defs.assets.transformations.sales_dbt_tasks import (
    REVENUE_SOURCE_NAME,
    revenue_dbt_gold_build,
    revenue_dbt_silver_build,
    revenue_dbt_source_freshness,
    revenue_dbt_source_tests,
    sales_pipeline,
)


@pytest.mark.unit
def test_sales_pipeline_is_none_or_pipeline():
    assert sales_pipeline is None or isinstance(sales_pipeline, DbtSourcePipeline)


@pytest.mark.unit
def test_sales_dbt_assets_are_conditional_on_dbt_project():
    for asset_def in (
        revenue_dbt_source_freshness,
        revenue_dbt_source_tests,
        revenue_dbt_silver_build,
        revenue_dbt_gold_build,
    ):
        assert asset_def is None or callable(asset_def)


@pytest.mark.unit
def test_revenue_source_steps_follow_naming_convention():
    if sales_pipeline is None:
        pytest.skip("dbt project/manifest unavailable")

    assert (
        revenue_dbt_source_freshness.key.to_user_string()
        == f"{REVENUE_SOURCE_NAME}_dbt_source_freshness"
    )
    assert (
        revenue_dbt_source_tests.key.to_user_string()
        == f"{REVENUE_SOURCE_NAME}_dbt_source_tests"
    )
