import logging

import pandas as pd

from src.clients.base_mlflow_client import BaseMLflowClient

logger = logging.getLogger(__name__)


class TopicClient(BaseMLflowClient):
    """MLflow client for the semantic journal topic extractor.

    Wraps the 'semantic_journal_topics' pyfunc model registered in MLflow.
    The underlying model uses KeyBERT + sentence-transformers (all-MiniLM-L6-v2)
    to extract semantically meaningful topics without relying on an external API.
    """

    def __init__(self) -> None:
        super().__init__(model_name="semantic_journal_topics")

    def extract_topics(self, text: str) -> list[dict]:
        """Extract topics from a single journal entry.

        Returns:
            List of topic dicts sorted by descending confidence:
            [{"topic_name": str, "confidence": float, "ml_model_version": str}, ...]
        """
        model_input = pd.DataFrame({"text": [text]})
        results: list[dict] = self.model.predict(model_input)
        return [{**topic, "ml_model_version": self.model_version} for topic in results[0]["topics"]]

    def extract_topics_batch(self, texts: list[str]) -> list[list[dict]]:
        """Extract topics for multiple journal entries in a single model call."""
        model_input = pd.DataFrame({"text": texts})
        results: list[dict] = self.model.predict(model_input)
        return [
            [{**topic, "ml_model_version": self.model_version} for topic in result["topics"]]
            for result in results
        ]

    def get_top_topic(self, text: str) -> dict | None:
        """Return the single highest-confidence topic for the given text."""
        topics = self.extract_topics(text)
        return topics[0] if topics else None
