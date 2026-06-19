from dagster import AssetSelection

from dagster_project.assets.exports.materialize_user_journal_features import (
    materialize_user_journal_features,
)
from dagster_project.assets.transformations.dbt_assets import dbt_gold_analytics
from dagster_project.jobs.utils import Audience, Domain, create_job, dbt_tag_selection

# Create a job that:
# 1. First runs dbt to build gold.user_journal_summary
# 2. Then materializes features to Redis via Feast

if dbt_gold_analytics is not None:
    # Select the analytics models (dbt_gold_analytics covers tag:analytics layer)
    analytics_selection = dbt_tag_selection([dbt_gold_analytics], tag="analytics")

    # Select the Feast materialization asset
    feast_asset_selection = AssetSelection.assets(materialize_user_journal_features)

    # Combine both selections - Dagster will respect dependencies
    # dbt will run first, then Feast materialization
    combined_selection = analytics_selection | feast_asset_selection

    materialize_feast_features_job = create_job(
        name="materialize_feast_features_job",
        selection=combined_selection,
        audience=Audience.USER_FACING,
        domain=Domain.FEATURE_STORE,
        pii=True,
        description=(
            "Builds dbt analytics models (including gold.user_journal_summary) "
            "and materializes features to Redis via Feast"
        ),
    )
else:
    materialize_feast_features_job = None
