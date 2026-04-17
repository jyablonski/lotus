import inspect
import logging
from typing import Any

import mlflow

from src.config import settings

# MLflow 3.x wraps pyfunc.load_model with @trace_disabled. That decorator can
# silently return None when our OTel HTTP provider overwrites the NoOp provider
# that MLflow installs, causing the re-enable() in the finally block to raise
# MlflowTracingException after result was already set — but a race in the
# wrapper loses the value. Bypass the decorator entirely with inspect.unwrap.
_pyfunc_load_model = inspect.unwrap(mlflow.pyfunc.load_model)

logger = logging.getLogger(__name__)


class BaseMLflowClient:
    """
    Base class for MLflow model clients.

    Handles common functionality for loading and managing MLflow pyfunc models,
    including model version resolution, metadata tracking, and readiness checks.
    """

    def __init__(
        self,
        model_name: str,
        mlflow_uri: str | None = None,
    ):
        """
        Initialize the MLflow client.

        Args:
            model_name: Name of the model in MLflow Model Registry
            mlflow_uri: Optional MLflow tracking URI (defaults to settings)
        """
        self.mlflow_uri = mlflow_uri or settings.mlflow_tracking_uri
        self.model = None
        self.model_version = None
        self.model_name = model_name
        self._is_loaded = False
        self.model_run_id = None

    def load_model(self, model_version: str = "latest"):
        """Load the MLflow pyfunc model and capture version info."""
        if self._is_loaded:
            return

        try:
            logger.info(f"Loading model {self.model_name}:{model_version} - {self.mlflow_uri}")
            mlflow.set_tracking_uri(self.mlflow_uri)

            model_uri = f"models:/{self.model_name}/{model_version}"
            logger.info(f"Calling _pyfunc_load_model({model_uri!r})...")
            self.model = _pyfunc_load_model(model_uri)
            logger.info(f"_pyfunc_load_model returned: {type(self.model)}")
            if self.model is None:
                raise RuntimeError(
                    f"mlflow.pyfunc.load_model returned None for {self.model_name} "
                    "even after bypassing @trace_disabled — unexpected MLflow 3.x state."
                )

            client = mlflow.MlflowClient(tracking_uri=self.mlflow_uri)
            if model_version == "latest":
                try:
                    all_versions = client.search_model_versions(f"name='{self.model_name}'")
                    if not all_versions:
                        raise ValueError(f"No versions found for model {self.model_name}")

                    latest_version = max(all_versions, key=lambda v: int(v.version))
                    self.model_version = latest_version.version
                    logger.info(f"Found latest model version: {self.model_version}")

                except Exception as e:
                    logger.warning(f"Could not determine latest version via API: {e}")
                    self.model_version = "latest"
            else:
                self.model_version = model_version

            try:
                model_version_details = client.get_model_version(
                    self.model_name, self.model_version
                )
                self.model_run_id = model_version_details.run_id
            except Exception as e:
                logger.warning(f"Could not get model run ID: {e}")
                self.model_run_id = "unknown"

            self._is_loaded = True
            logger.info(
                f"Model loaded successfully - Version: {self.model_version}, "
                f"Run ID: {self.model_run_id}"
            )

        except Exception as e:
            logger.error(
                f"Failed to load MLflow model {self.model_name}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            raise

    def get_model_info(self) -> dict[str, Any]:
        """Get current model information."""
        if not self.is_ready():
            return {"status": "not_loaded"}

        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "run_id": self.model_run_id,
            "mlflow_uri": self.mlflow_uri,
            "status": "loaded",
        }

    def is_ready(self) -> bool:
        """Check if the model is loaded and ready to use."""
        ready = self._is_loaded and self.model is not None
        if not ready:
            logger.warning(
                f"is_ready=False for {self.model_name}: "
                f"_is_loaded={self._is_loaded}, model={self.model!r}"
            )
        return ready
