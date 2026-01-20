import os
from pathlib import Path
from contextlib import contextmanager

from dagster import ConfigurableResource
from feast import FeatureStore


class FeastResource(ConfigurableResource):
    """Feast feature store resource for managing feature materialization."""

    repo_path: str
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    def get_feature_store(self) -> FeatureStore:
        """Get a Feast FeatureStore instance."""
        return FeatureStore(repo_path=self.repo_path)

    @contextmanager
    def get_store(self):
        """Context manager for FeatureStore."""
        store = self.get_feature_store()
        try:
            yield store
        finally:
            # Feast stores don't need explicit cleanup, but we can add it if needed
            pass


# Default Feast resource instance
# The repo_path should point to the directory containing feature_store.yaml
# In Docker: /app/feast_repo
# Locally: services/dagster/feast_repo (relative to project root)
if os.getenv("DAGSTER_CURRENT_IMAGE"):
    # Running in Docker - use absolute path
    repo_path = "/app/feast_repo"
else:
    # Running locally - use path relative to this file
    repo_path = str(Path(__file__).parent.parent.parent.parent / "feast_repo")

feast_store = FeastResource(
    repo_path=repo_path,
    redis_host=os.getenv("REDIS_HOST", "redis"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    redis_password=os.getenv("REDIS_PASSWORD"),
)
