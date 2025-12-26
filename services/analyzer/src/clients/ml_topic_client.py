import logging
from typing import Any

import pandas as pd

from src.clients.base_mlflow_client import BaseMLflowClient

logger = logging.getLogger(__name__)


class TopicClient(BaseMLflowClient):
    """
    Client for topic extraction using MLflow pyfunc models.

    The loaded model is a pyfunc wrapper that handles all preprocessing
    and returns formatted topic predictions directly.
    """

    def __init__(
        self,
        mlflow_uri: str | None = None,
    ):
        super().__init__(model_name="adaptive_journal_topics", mlflow_uri=mlflow_uri)

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
