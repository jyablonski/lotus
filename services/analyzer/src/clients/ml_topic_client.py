import logging
import os
from typing import Any

import mlflow
import pandas as pd

logger = logging.getLogger(__name__)


class TopicClient:
    """
    Client for topic extraction using MLflow pyfunc models.

    The loaded model is a pyfunc wrapper that handles all preprocessing
    and returns formatted topic predictions directly.
    """

    def __init__(
        self,
        mlflow_uri: str = os.environ.get("MLFLOW_CONN_URI", "http://localhost:5000"),
    ):
        self.mlflow_uri = mlflow_uri
        self.model = None
        self.model_version = None
        self.model_name = "adaptive_journal_topics"
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
            self.model = mlflow.pyfunc.load_model(model_uri)

            # Get actual model version info
            client = mlflow.MlflowClient()
            if model_version == "latest":
                try:
                    all_versions = client.search_model_versions(f"name='{self.model_name}'")
                    if not all_versions:
                        raise ValueError(f"No versions found for model {self.model_name}")

                    latest_version = max(all_versions, key=lambda v: int(v.version))
                    self.model_version = latest_version.version
                    logger.info(f"Found latest version: {self.model_version}")

                except Exception as e:
                    logger.warning(f"Could not determine latest version via API: {e}")
                    self.model_version = "latest"
            else:
                self.model_version = model_version

            # Get additional model metadata
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
            logger.error(f"Failed to load MLflow model: {e}")
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
        return self._is_loaded and self.model is not None

    def extract_topics(self, text: str) -> list[dict[str, Any]]:
        """
        Extract topics from text using the pyfunc model.

        The model handles adaptive topic extraction based on text length
        and returns formatted results directly.

        Returns:
            List of topic dicts with topic_id, topic_name, confidence, and ml_model_version
        """
        if not self.is_ready():
            raise RuntimeError("TopicClient model not loaded. Call load_model() first.")

        # Create DataFrame input for pyfunc model
        input_df = pd.DataFrame({"text": [text]})

        # Model returns list of dicts with "topics" key
        results = self.model.predict(input_df)

        # Extract topics from first result and add model version
        topics = results[0].get("topics", []) if results else []

        # Add model version to each topic
        for topic in topics:
            topic["ml_model_version"] = self.model_version

        return topics

    def extract_topics_batch(self, texts: list[str]) -> list[list[dict[str, Any]]]:
        """
        Extract topics from multiple texts.

        Returns:
            List of topic lists, one per input text
        """
        if not self.is_ready():
            raise RuntimeError("TopicClient model not loaded. Call load_model() first.")

        input_df = pd.DataFrame({"text": texts})
        results = self.model.predict(input_df)

        # Add model version to each topic in each result
        all_topics = []
        for result in results:
            topics = result.get("topics", [])
            for topic in topics:
                topic["ml_model_version"] = self.model_version
            all_topics.append(topics)

        return all_topics

    def get_top_topic(self, text: str) -> dict[str, Any]:
        """Get just the most likely topic."""
        topics = self.extract_topics(text)

        if topics:
            return topics[0]

        return {
            "topic_name": "Other",
            "confidence": 0.0,
            "reason": "No topics extracted",
            "ml_model_version": self.model_version,
        }
