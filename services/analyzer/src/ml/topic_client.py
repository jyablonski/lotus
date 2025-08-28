import logging
import os
from typing import Any

import mlflow

logger = logging.getLogger(__name__)


class TopicClient:
    def __init__(
        self,
        mlflow_uri: str = os.environ.get("MLFLOW_CONN_URI", "http://localhost:5000"),
    ):
        self.mlflow_uri = mlflow_uri
        self.model = None
        self.model_version = None
        self.model_name = "adaptive_journal_topics"
        self._is_loaded = False

        # Based on your word analysis
        self.topic_labels = {
            0: "Daily Needs & Work",
            1: "Evening Reflection",
            2: "Work & Productivity",
            3: "Emotional State",
            4: "Feelings & Emotions",
            5: "Daily Activities",
            6: "Morning Routine & Positivity",
            7: "Work Focus & Effort",
        }

        # Thresholds for classification
        self.min_confidence_threshold = 0.2
        self.max_confidence_threshold = 0.4

    def load_model(self, model_version: str = "latest"):
        """Load the MLflow model and capture version info."""
        if self._is_loaded:
            return

        try:
            logger.info(
                f"Loading model {self.model_name}:{model_version} from {self.mlflow_uri}"
            )
            mlflow.set_tracking_uri(self.mlflow_uri)

            model_uri = f"models:/{self.model_name}/{model_version}"
            self.model = mlflow.sklearn.load_model(model_uri)

            # Get actual model version info
            client = mlflow.MlflowClient()
            if model_version == "latest":
                # Use the modern approach to get the latest version
                try:
                    # Get all versions and find the latest one
                    all_versions = client.search_model_versions(
                        f"name='{self.model_name}'"
                    )
                    if not all_versions:
                        raise ValueError(
                            f"No versions found for model {self.model_name}"
                        )

                    # Sort by version number (descending) to get the latest
                    latest_version = max(all_versions, key=lambda v: int(v.version))
                    self.model_version = latest_version.version
                    logger.info(f"Found latest version: {self.model_version}")

                except Exception as e:
                    # Fallback: use 'latest' as version identifier
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

    def extract_topics(
        self, text: str, min_confidence=0.1, include_other=True
    ) -> list[dict[str, Any]]:
        """Extract topics with names, including 'Other' category and model version."""
        if not self.is_ready():
            raise RuntimeError("TopicClient model not loaded. Call load_model() first.")

        probs = self.model.transform([text])[0]
        max_confidence = probs.max()

        results = []

        # Check if we should classify as "Other"
        if include_other and max_confidence < self.max_confidence_threshold:
            reason = (
                f"Highest confidence ({max_confidence:.1%}) "
                f"below threshold ({self.max_confidence_threshold:.1%})"
            )
            results.append(
                {
                    "topic_name": "Other",
                    "confidence": float(max_confidence),
                    "reason": reason,
                    "ml_model_version": self.model_version,
                }
            )
            return results

        # Normal topic classification
        for topic_id, confidence in enumerate(probs):
            if confidence >= min_confidence:
                results.append(
                    {
                        "topic_name": self.topic_labels[topic_id],
                        "confidence": float(confidence),
                        "ml_model_version": self.model_version,
                    }
                )

        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def get_top_topic(self, text: str) -> dict[str, Any]:
        """Get just the most likely topic (including 'Other')"""
        topics = self.extract_topics(text, min_confidence=0.0, include_other=True)
        return (
            topics[0]
            if topics
            else {
                "topic_name": "Other",
                "confidence": 0.0,
                "reason": "No classification possible",
                "ml_model_version": self.model_version,
            }
        )

    def classify_with_confidence_check(self, text: str) -> dict[str, Any]:
        """
        Classify text with confidence analysis
        Returns the top topic or 'Other' if confidence is too low
        """
        if not self.is_ready():
            raise RuntimeError("TopicClient model not loaded. Call load_model() first.")

        probs = self.model.transform([text])[0]
        max_confidence = probs.max()
        top_topic_id = probs.argmax()

        base_result = {
            "confidence": float(max_confidence),
            "ml_model_version": self.model_version,
        }

        if max_confidence < self.max_confidence_threshold:
            details = (
                f'Best match was "{self.topic_labels[top_topic_id]}" '
                f"at {max_confidence:.1%}"
            )
            return {
                **base_result,
                "topic_name": "Other",
                "reason": "Low confidence classification",
                "details": details,
            }

        return {
            **base_result,
            "topic_name": self.topic_labels[top_topic_id],
            "reason": "High confidence classification",
        }
