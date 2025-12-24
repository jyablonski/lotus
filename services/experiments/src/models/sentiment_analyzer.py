import re
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


class JournalSentimentAnalyzer:
    """
    Sentiment analyzer specifically tuned for journal entries.
    Classifies entries into positive, negative, or neutral sentiment.
    """

    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version
        self.sentiment_pipeline = None
        self.sentiment_labels = {0: "negative", 1: "neutral", 2: "positive"}
        self.confidence_thresholds = {"high": 0.7, "medium": 0.5, "low": 0.3}

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Keep punctuation as it can be important for sentiment
        text = text.strip()

        return text

    def train(self, training_data: list[dict[str, Any]]):
        """
        Train the sentiment model

        Args:
            training_data: list of dicts with 'text' and 'sentiment' keys
                          sentiment should be 'positive', 'negative', or 'neutral'
        """
        texts = []
        labels = []

        # Reverse mapping for labels
        label_to_num = {v: k for k, v in self.sentiment_labels.items()}

        for item in training_data:
            processed_text = self._preprocess_text(item["text"])
            texts.append(processed_text)
            labels.append(label_to_num[item["sentiment"]])

        # Create pipeline
        self.sentiment_pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=5000,
                        ngram_range=(1, 2),
                        stop_words="english",
                        lowercase=True,
                        min_df=2,
                    ),
                ),
                ("classifier", MultinomialNB(alpha=0.1)),
            ]
        )

        # Train the model
        self.sentiment_pipeline.fit(texts, labels)

        print(f"Sentiment model v{self.model_version} trained on {len(texts)} samples")

    def predict_sentiment(self, text: str) -> dict[str, Any]:
        """
        Predict sentiment of a single journal entry

        Returns:
            dict with sentiment, confidence, and confidence_level
        """
        if not self.sentiment_pipeline:
            raise ValueError("Model must be trained before making predictions")

        processed_text = self._preprocess_text(text)

        # Get prediction and probabilities
        prediction = self.sentiment_pipeline.predict([processed_text])[0]
        probabilities = self.sentiment_pipeline.predict_proba([processed_text])[0]

        sentiment = self.sentiment_labels[prediction]
        confidence = float(max(probabilities))

        # Determine confidence level
        if confidence >= self.confidence_thresholds["high"]:
            confidence_level = "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "all_scores": {
                self.sentiment_labels[i]: float(prob) for i, prob in enumerate(probabilities)
            },
        }

    def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Predict sentiment for multiple entries"""
        return [self.predict_sentiment(text) for text in texts]

    def analyze_sentiment_trends(self, entries_with_dates: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze sentiment trends over time

        Args:
            entries_with_dates: list of dicts with 'text' and 'date' keys
        """
        results = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_confidence = 0

        for entry in entries_with_dates:
            sentiment_result = self.predict_sentiment(entry["text"])
            sentiment_result["date"] = entry["date"]
            results.append(sentiment_result)

            sentiment_counts[sentiment_result["sentiment"]] += 1
            total_confidence += sentiment_result["confidence"]

        avg_confidence = total_confidence / len(entries_with_dates) if entries_with_dates else 0

        return {
            "individual_results": results,
            "overall_distribution": sentiment_counts,
            "average_confidence": avg_confidence,
            "dominant_sentiment": max(sentiment_counts, key=sentiment_counts.get),
            "total_entries": len(entries_with_dates),
        }

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the trained model"""
        if not self.sentiment_pipeline:
            return {"status": "not_trained"}

        tfidf = self.sentiment_pipeline.named_steps["tfidf"]

        return {
            "model_version": self.model_version,
            "status": "trained",
            "vocabulary_size": len(tfidf.vocabulary_) if hasattr(tfidf, "vocabulary_") else 0,
            "sentiment_labels": list(self.sentiment_labels.values()),
            "confidence_thresholds": self.confidence_thresholds,
        }
