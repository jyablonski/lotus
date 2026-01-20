from datetime import datetime, timezone
import sys
from pathlib import Path
from dagster import AssetExecutionContext, asset
from dagster_project.resources import FeastResource


@asset(
    group_name="exports",
    description="Materialize user_journal_summary features from gold schema to Redis via Feast",
)
def materialize_user_journal_features(
    context: AssetExecutionContext,
    feast_store: FeastResource,
) -> dict:
    """Materialize user_journal_summary features to Redis using Feast."""

    with feast_store.get_store() as store:
        feature_view_name = "user_journal_summary_features"

        # Try to get the feature view, apply if it doesn't exist
        try:
            fv = store.get_feature_view(feature_view_name)
            context.log.info(f"Found feature view: {fv.name}")
        except Exception:
            # Feature view not found, need to apply it
            context.log.info(
                f"Feature view '{feature_view_name}' not found, applying to registry..."
            )
            
            # Import and apply feature views from the repo
            repo_path = Path(feast_store.repo_path)
            
            # Add repo path to Python path temporarily
            if str(repo_path) not in sys.path:
                sys.path.insert(0, str(repo_path))
            
            try:
                # Import entities and feature views
                from entities import user_entity
                from feature_views import user_journal_summary_fv
                
                # Apply them to the registry
                store.apply([user_entity, user_journal_summary_fv])
                context.log.info("Feature views applied successfully")
                
                # Now get the feature view
                fv = store.get_feature_view(feature_view_name)
            except Exception as e:
                # Remove from path if we added it
                if str(repo_path) in sys.path:
                    sys.path.remove(str(repo_path))
                raise ValueError(f"Failed to apply feature views: {e}") from e
            finally:
                # Clean up sys.path
                if str(repo_path) in sys.path:
                    sys.path.remove(str(repo_path))

        # Log config for debugging
        context.log.info(f"Online store config: {store.config.online_store}")
        context.log.info(f"Offline store config: {store.config.offline_store}")

        # Wide time range to capture all data
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end_date = datetime.now(timezone.utc)

        context.log.info(
            f"Materializing {feature_view_name} from {start_date} to {end_date}"
        )

        # Run materialization
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
