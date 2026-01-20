from dagster import AssetSelection, define_asset_job
from dagster_dbt import build_dbt_asset_selection

from dagster_project.assets.transformations.dbt_assets import dbt_analytics

# Create a job that:
# 1. First runs dbt to build gold.user_journal_summary
# 2. Then materializes features to Redis via Feast

if dbt_analytics is not None:
    # Select the analytics models (which includes gold.user_journal_summary)
    analytics_selection = build_dbt_asset_selection(
        [dbt_analytics], dbt_select="tag:analytics"
    )

    # Select the Feast materialization asset
    feast_asset_selection = AssetSelection.assets("materialize_user_journal_features")

    # Combine both selections - Dagster will respect dependencies
    # dbt will run first, then Feast materialization
    combined_selection = analytics_selection | feast_asset_selection

    materialize_feast_features_job = define_asset_job(
        name="materialize_feast_features_job",
        selection=combined_selection,
        description=(
            "Builds dbt analytics models (including gold.user_journal_summary) "
            "and materializes features to Redis via Feast"
        ),
    )
else:
    materialize_feast_features_job = None
