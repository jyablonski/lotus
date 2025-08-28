import logging
import os
import time

import mlflow
import mlflow.sklearn


class MLTopicClient:
    """Client for connecting to MLFlow and pulling models"""

    def __init__(
        self, mlflow_uri=os.environ.get("MLFLOW_CONN_URI", "http://mlflow:5000")
    ):
        """Initialize the MLTopicClient."""
        logging.info("Sleeping 10")
        time.sleep(10)  # Wait for MLflow server to be ready
        logging.info(f"Connecting to MLflow at {mlflow_uri}")
        mlflow.set_tracking_uri(mlflow_uri)
        self.model = None
        self.load_latest_model()

    def load_latest_model(self, max_retries=5):
        """Loads the latest version with retry logic"""
        model_uri = "models:/adaptive_journal_topics/latest"

        for attempt in range(max_retries):
            try:
                self.model = mlflow.sklearn.load_model(model_uri)
                logging.info(f"Successfully loaded model on attempt {attempt + 1}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logging.warning(
                        f"Failed to load model (attempt {attempt + 1}): {e}"
                    )
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise e

    def extract_topic_probabilities(self, text: str):
        """Extract topic probabilities from the model for a given text.

        Args:
            text (str): The input text to analyze.

        Returns:
            np.ndarray: An array of topic probabilities for the input text.
        """
        # This returns the raw LDA probabilities
        return self.model.transform([text])[0]
