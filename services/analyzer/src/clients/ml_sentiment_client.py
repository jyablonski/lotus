import logging
from typing import Any

import pandas as pd

from src.clients.base_mlflow_client import BaseMLflowClient

logger = logging.getLogger(__name__)


class SentimentClient(BaseMLflowClient):
    """
    Client for sentiment analysis using MLflow pyfunc models.

    The loaded model is a pyfunc wrapper that handles all preprocessing
    and returns formatted sentiment predictions directly.
    """

    def __init__(
        self,
        mlflow_uri: str | None = None,
    ):
        super().__init__(model_name="journal_sentiment_analyzer", mlflow_uri=mlflow_uri)
        # Minimum confidence for reliable classification
        self.min_confidence_threshold = 0.4

    def predict_sentiment(self, text: str) -> dict[str, Any]:
        """
        Predict sentiment of a single journal entry.

        The model handles all preprocessing and returns formatted results
        with sentiment, confidence, confidence_level, and all_scores.

        Returns:
            Dict with sentiment prediction and metadata
        """
        if not self.is_ready():
            raise RuntimeError("SentimentClient model not loaded. Call load_model() first.")

        # Create DataFrame input for pyfunc model
        input_df = pd.DataFrame({"text": [text]})

        # Model returns list of prediction dicts
        results = self.model.predict(input_df)
        result = results[0] if results else {}

        # Add model version and reliability check
        confidence = result.get("confidence", 0.0)
        is_reliable = confidence >= self.min_confidence_threshold

        return {
            "sentiment": result.get("sentiment", "unknown"),
            "confidence": confidence,
            "confidence_level": result.get("confidence_level", "low"),
            "is_reliable": is_reliable,
            "all_scores": result.get("all_scores", {}),
            "ml_model_version": self.model_version,
            "reason": "High confidence classification"
            if is_reliable
            else "Low confidence - consider as uncertain",
        }

    def predict_sentiment_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Predict sentiment for multiple entries."""
        if not self.is_ready():
            raise RuntimeError("SentimentClient model not loaded. Call load_model() first.")

        input_df = pd.DataFrame({"text": texts})
        results = self.model.predict(input_df)

        # Add model version and reliability check to each result
        processed_results = []
        for result in results:
            confidence = result.get("confidence", 0.0)
            is_reliable = confidence >= self.min_confidence_threshold

            processed_results.append(
                {
                    "sentiment": result.get("sentiment", "unknown"),
                    "confidence": confidence,
                    "confidence_level": result.get("confidence_level", "low"),
                    "is_reliable": is_reliable,
                    "all_scores": result.get("all_scores", {}),
                    "ml_model_version": self.model_version,
                    "reason": "High confidence classification"
                    if is_reliable
                    else "Low confidence - consider as uncertain",
                }
            )

        return processed_results

    def get_sentiment_simple(self, text: str) -> str:
        """Get just the sentiment label (positive/negative/neutral)."""
        result = self.predict_sentiment(text)
        return result["sentiment"]

    def classify_with_confidence_check(self, text: str) -> dict[str, Any]:
        """
        Classify text with confidence analysis.
        Returns sentiment or 'uncertain' if confidence is too low.
        """
        result = self.predict_sentiment(text)

        if not result["is_reliable"]:
            return {
                "sentiment": "uncertain",
                "confidence": result["confidence"],
                "confidence_level": result["confidence_level"],
                "reason": f"Low confidence ({result['confidence']:.1%}) - best guess was {result['sentiment']}",
                "details": f"Confidence below threshold ({self.min_confidence_threshold:.1%})",
                "ml_model_version": self.model_version,
                "original_prediction": result["sentiment"],
            }

        return {
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
            "confidence_level": result["confidence_level"],
            "reason": "High confidence classification",
            "ml_model_version": self.model_version,
        }

    def analyze_sentiment_trends(self, entries_with_dates: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze sentiment trends over time.

        Args:
            entries_with_dates: List of dicts with 'text' and 'date' keys
        """
        if not self.is_ready():
            raise RuntimeError("SentimentClient model not loaded. Call load_model() first.")

        # Batch predict all sentiments
        texts = [entry["text"] for entry in entries_with_dates]
        predictions = self.predict_sentiment_batch(texts)

        # Combine predictions with dates
        results = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "uncertain": 0}
        total_confidence = 0
        reliable_predictions = 0

        for i, prediction in enumerate(predictions):
            prediction["date"] = entries_with_dates[i]["date"]
            results.append(prediction)

            if prediction["is_reliable"]:
                sentiment_counts[prediction["sentiment"]] += 1
                reliable_predictions += 1
            else:
                sentiment_counts["uncertain"] += 1

            total_confidence += prediction["confidence"]

        avg_confidence = total_confidence / len(entries_with_dates) if entries_with_dates else 0
        reliability_rate = (
            reliable_predictions / len(entries_with_dates) if entries_with_dates else 0
        )

        # Determine dominant sentiment (excluding uncertain)
        reliable_counts = {k: v for k, v in sentiment_counts.items() if k != "uncertain"}
        dominant_sentiment = (
            max(reliable_counts, key=reliable_counts.get)
            if any(reliable_counts.values())
            else "uncertain"
        )

        return {
            "individual_results": results,
            "overall_distribution": sentiment_counts,
            "average_confidence": avg_confidence,
            "reliability_rate": reliability_rate,
            "dominant_sentiment": dominant_sentiment,
            "total_entries": len(entries_with_dates),
            "ml_model_version": self.model_version,
            "analysis_summary": {
                "most_common": dominant_sentiment,
                "reliability": f"{reliability_rate:.1%}",
                "avg_confidence": f"{avg_confidence:.1%}",
            },
        }
