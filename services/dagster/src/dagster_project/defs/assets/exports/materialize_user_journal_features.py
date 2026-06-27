from datetime import datetime, timezone
import sys
from pathlib import Path
from dagster import AssetExecutionContext, AssetKey, asset
from dagster_project.resources import FeastResource


@asset(
    group_name="exports",
    deps=[AssetKey(["gold", "user_journal_summary"])],
    description="Materialize user_journal_summary features from gold schema to Redis via Feast",
)
def materialize_user_journal_features(
    context: AssetExecutionContext,
    feast_store: FeastResource,
) -> dict:
    """Materialize user_journal_summary features to Redis using Feast."""

    with feast_store.get_store() as store:
        feature_view_name = "user_journal_summary_features"

        # Feature views are persisted in Postgres under `feast.feature_views`.
        # If this is a fresh environment the view won't exist yet, so fall back
        # to applying it from the repo-local definitions.
        try:
            fv = store.get_feature_view(feature_view_name)
            context.log.info(f"Found feature view: {fv.name}")
        except Exception:
            context.log.info(
                f"Feature view '{feature_view_name}' not found, applying to registry..."
            )

            # The feast repo isn't on sys.path by default; temporarily add it so
            # we can import the entity/feature-view definitions, then clean up.
            repo_path = Path(feast_store.repo_path)
            if str(repo_path) not in sys.path:
                sys.path.insert(0, str(repo_path))

            try:
                from entities import user_entity
                from feature_views import user_journal_summary_fv

                store.apply([user_entity, user_journal_summary_fv])
                context.log.info("Feature views applied successfully")

                fv = store.get_feature_view(feature_view_name)
            except Exception as e:
                if str(repo_path) in sys.path:
                    sys.path.remove(str(repo_path))
                raise ValueError(f"Failed to apply feature views: {e}") from e
            finally:
                if str(repo_path) in sys.path:
                    sys.path.remove(str(repo_path))

        context.log.info(f"Online store config: {store.config.online_store}")
        context.log.info(f"Offline store config: {store.config.offline_store}")

        # Use a wide time range so we pick up historical rows on first run.
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end_date = datetime.now(timezone.utc)

        context.log.info(
            f"Materializing {feature_view_name} from {start_date} to {end_date}"
        )

        store.materialize(
            feature_views=[feature_view_name],
            start_date=start_date,
            end_date=end_date,
        )

        context.log.info("Materialization complete")

        return {
            "status": "success",
            "feature_view": feature_view_name,
            "materialized_at": end_date.isoformat(),
        }
