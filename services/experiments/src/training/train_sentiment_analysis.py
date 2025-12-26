"""
Sentiment Analysis Training - Journal Entries
Uses sklearn Pipeline with TfidfVectorizer and MLflow pyfunc wrapper for production deployment.
"""

import os
import tempfile
from typing import Any

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder


class SentimentAnalyzerWrapper(mlflow.pyfunc.PythonModel):
    """
    Production wrapper for sentiment analysis that:
    1. Loads the sklearn pipeline and label encoder on startup
    2. Provides predict method for single/batch text classification
    3. Returns formatted output with sentiment labels and confidence scores
    """

    def load_context(self, context):
        """
        Called once when model is loaded (e.g., server startup).
        Load artifacts from MLflow.

        Available in context.artifacts:
            - "sklearn_pipeline": path to saved sklearn pipeline
            - "label_encoder": path to saved label encoder
            - "sentiment_labels": path to sentiment labels mapping
        """
        self.pipeline = mlflow.sklearn.load_model(context.artifacts["sklearn_pipeline"])

        # Load label encoder
        import pickle

        with open(context.artifacts["label_encoder"], "rb") as f:
            self.label_encoder = pickle.load(f)

        # Load sentiment labels mapping
        self.sentiment_labels = pd.read_parquet(context.artifacts["sentiment_labels"])
        self._label_map = dict(
            zip(
                self.sentiment_labels["label_id"], self.sentiment_labels["label_name"], strict=False
            )
        )

        self.confidence_thresholds = {"high": 0.7, "medium": 0.5, "low": 0.3}

    def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
        """
        Predict sentiment for journal entries.

        Args:
            context: MLflow context (unused here, artifacts already loaded)
            model_input: DataFrame with column:
                - text (required): The journal entry text

        Returns:
            List of prediction dicts, one per input row:
            [{"sentiment": "positive", "confidence": 0.85, "confidence_level": "high", "all_scores": {...}}, ...]
        """
        if "text" not in model_input.columns:
            raise ValueError("model_input must contain 'text' column")

        texts = model_input["text"].tolist()
        results = []

        for text in texts:
            result = self._predict_single(text)
            results.append(result)

        return results

    def _predict_single(self, text: str) -> dict[str, Any]:
        """Predict sentiment for a single text."""
        # Preprocess text
        processed_text = self._preprocess_text(text)

        # Get prediction and probabilities
        prediction = self.pipeline.predict([processed_text])[0]
        probabilities = self.pipeline.predict_proba([processed_text])[0]

        sentiment = self._label_map[prediction]
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
            "confidence": round(confidence, 4),
            "confidence_level": confidence_level,
            "all_scores": {
                self._label_map[i]: round(float(prob), 4) for i, prob in enumerate(probabilities)
            },
        }

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis."""
        import re

        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Predict sentiment for multiple texts (convenience method)."""
        df = pd.DataFrame({"text": texts})
        return self.predict(None, df)

    def analyze_sentiment_trends(self, entries_with_dates: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze sentiment trends over time.

        Args:
            entries_with_dates: list of dicts with 'text' and 'date' keys
        """
        texts = [entry["text"] for entry in entries_with_dates]
        predictions = self.predict_batch(texts)

        results = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_confidence = 0

        for i, entry in enumerate(entries_with_dates):
            pred = predictions[i]
            pred["date"] = entry["date"]
            results.append(pred)

            sentiment_counts[pred["sentiment"]] += 1
            total_confidence += pred["confidence"]

        avg_confidence = total_confidence / len(entries_with_dates) if entries_with_dates else 0

        return {
            "individual_results": results,
            "overall_distribution": sentiment_counts,
            "average_confidence": round(avg_confidence, 4),
            "dominant_sentiment": max(sentiment_counts, key=sentiment_counts.get),
            "total_entries": len(entries_with_dates),
        }


def get_training_data():
    """Get labeled training data for sentiment analysis."""
    return [
        # Positive entries
        {
            "text": "Today was incredibly productive at work. Finished the quarterly report and got positive feedback from my manager.",
            "sentiment": "positive",
        },
        {
            "text": "Had a wonderful dinner with family. Grateful for these moments of connection and love.",
            "sentiment": "positive",
        },
        {
            "text": "Great workout at the gym this morning! Feel energized and accomplished.",
            "sentiment": "positive",
        },
        {
            "text": "Surprised myself by how well the meeting went. Felt confident and prepared.",
            "sentiment": "positive",
        },
        {
            "text": "Beautiful weather inspired a long walk in nature. Feeling peaceful and refreshed.",
            "sentiment": "positive",
        },
        {
            "text": "Proud of finishing that challenging project. The hard work really paid off.",
            "sentiment": "positive",
        },
        {
            "text": "Simple morning routine of coffee and journaling sets a positive tone for the day.",
            "sentiment": "positive",
        },
        {
            "text": "Finally got that promotion I've been working towards! So excited for this new chapter.",
            "sentiment": "positive",
        },
        {
            "text": "Spent the day volunteering and it felt amazing to give back to the community.",
            "sentiment": "positive",
        },
        {
            "text": "Discovered a new hobby today and I'm already passionate about it!",
            "sentiment": "positive",
        },
        # Negative entries
        {
            "text": "Feeling anxious about tomorrow's presentation. Spent the evening preparing but still worried.",
            "sentiment": "negative",
        },
        {
            "text": "Struggled with motivation today. Everything felt overwhelming and I couldn't focus on anything.",
            "sentiment": "negative",
        },
        {
            "text": "Work stress is really getting to me. Need to find better ways to manage the pressure.",
            "sentiment": "negative",
        },
        {
            "text": "Missing my friends who live far away. Technology helps but it's not the same as being together.",
            "sentiment": "negative",
        },
        {
            "text": "Frustrated with my sleep schedule. Need to be more disciplined about bedtime routines.",
            "sentiment": "negative",
        },
        {
            "text": "Dealing with relationship conflicts is draining but necessary for growth.",
            "sentiment": "negative",
        },
        {
            "text": "Had a terrible argument with my partner today. Feeling hurt and confused.",
            "sentiment": "negative",
        },
        {
            "text": "The rejection letter arrived today. Disappointed but trying to stay motivated.",
            "sentiment": "negative",
        },
        {
            "text": "Feeling lonely even when surrounded by people. Something feels missing.",
            "sentiment": "negative",
        },
        {
            "text": "Health issues are causing me anxiety and affecting my daily life.",
            "sentiment": "negative",
        },
        # Neutral entries
        {
            "text": "Spent a quiet evening reading and drinking tea. Sometimes simple pleasures are the best.",
            "sentiment": "neutral",
        },
        {
            "text": "Learned something new about myself today through a difficult conversation.",
            "sentiment": "neutral",
        },
        {
            "text": "Routine day at the office. Nothing particularly exciting or troublesome happened.",
            "sentiment": "neutral",
        },
        {
            "text": "Went grocery shopping and did some meal prep for the week.",
            "sentiment": "neutral",
        },
        {
            "text": "Watched a documentary about ocean conservation. Informative but not life-changing.",
            "sentiment": "neutral",
        },
        {"text": "Did some household chores and organized my workspace.", "sentiment": "neutral"},
        {
            "text": "Had a regular catch-up call with my sister. Nice to stay connected.",
            "sentiment": "neutral",
        },
        {
            "text": "Finished reading a book that was okay but didn't really resonate with me.",
            "sentiment": "neutral",
        },
        {
            "text": "Attended a work meeting that was necessary but unremarkable.",
            "sentiment": "neutral",
        },
        {
            "text": "Took a walk around the neighborhood. The weather was mild and pleasant.",
            "sentiment": "neutral",
        },
        # Additional mixed sentiment for better training
        {
            "text": "Work was stressful but I managed to complete my tasks and felt accomplished.",
            "sentiment": "neutral",
        },
        {
            "text": "The movie was disappointing, but spending time with friends made up for it.",
            "sentiment": "neutral",
        },
        {
            "text": "Mixed feelings about the changes at work. Excited for new opportunities but nervous too.",
            "sentiment": "neutral",
        },
    ]


def build_sentiment_pipeline() -> Pipeline:
    """Build sklearn pipeline for sentiment analysis."""
    pipeline = Pipeline(
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
    return pipeline


def train_and_register():
    """Train and register the sentiment analysis model."""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("journal_sentiment_analysis")

    # Get training data
    training_data = get_training_data()

    with mlflow.start_run(run_name="sentiment_analyzer"):
        # Prepare data
        texts = [item["text"] for item in training_data]
        sentiments = [item["sentiment"] for item in training_data]

        # Encode labels
        label_encoder = LabelEncoder()
        labels = label_encoder.fit_transform(sentiments)

        # Create sentiment labels dataframe
        sentiment_labels_df = pd.DataFrame(
            {
                "label_id": range(len(label_encoder.classes_)),
                "label_name": label_encoder.classes_,
            }
        )

        # Split data for validation
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # Build and train pipeline
        pipeline = build_sentiment_pipeline()
        pipeline.fit(X_train, y_train)

        # Log parameters
        mlflow.log_param("model_type", "multinomial_nb")
        mlflow.log_param("training_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("sentiment_classes", len(label_encoder.classes_))

        # Evaluate
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        y_proba = pipeline.predict_proba(X_test)
        avg_confidence = float(np.mean(np.max(y_proba, axis=1)))

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("avg_confidence", avg_confidence)

        print(f"Model Accuracy: {accuracy:.3f}")
        print(f"Average Confidence: {avg_confidence:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

        # Test with sample cases
        test_cases = [
            "I feel amazing today! Everything is going perfectly.",
            "I'm worried about the future and feel overwhelmed.",
            "Had a normal day. Nothing special happened.",
            "Work was challenging but I learned a lot and feel proud of my progress.",
            "I hate everything about this situation and feel completely defeated.",
        ]

        print("\nTest Case Results:")
        for i, test_text in enumerate(test_cases, 1):
            pred = pipeline.predict([test_text.lower()])[0]
            proba = pipeline.predict_proba([test_text.lower()])[0]
            sentiment = label_encoder.classes_[pred]
            confidence = max(proba)
            mlflow.log_metric(f"test_case_{i}_confidence", confidence)
            print(f"{i}. '{test_text[:50]}...' -> {sentiment} ({confidence:.3f})")

        # Save artifacts to temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save the sklearn pipeline
            sklearn_path = os.path.join(tmp_dir, "sklearn_pipeline")
            mlflow.sklearn.save_model(pipeline, sklearn_path)

            # Save label encoder
            import pickle

            label_encoder_path = os.path.join(tmp_dir, "label_encoder.pkl")
            with open(label_encoder_path, "wb") as f:
                pickle.dump(label_encoder, f)

            # Save sentiment labels
            sentiment_labels_path = os.path.join(tmp_dir, "sentiment_labels.parquet")
            sentiment_labels_df.to_parquet(sentiment_labels_path, index=False)

            # Define artifact paths for the wrapper
            artifact_paths = {
                "sklearn_pipeline": sklearn_path,
                "label_encoder": label_encoder_path,
                "sentiment_labels": sentiment_labels_path,
            }

            # Log the complete model with wrapper
            print("Logging model with pyfunc wrapper...")
            mlflow.pyfunc.log_model(
                artifact_path="sentiment_model",
                python_model=SentimentAnalyzerWrapper(),
                artifacts=artifact_paths,
                code_paths=[__file__],
                pip_requirements=[
                    "pandas",
                    "numpy",
                    "scikit-learn",
                    "mlflow",
                    "pyarrow",
                ],
                registered_model_name="journal_sentiment_analyzer",
            )
            print("Model logged successfully!")

        # Demonstrate trend analysis capability
        print("\nSample trend analysis:")
        sample_entries = [
            {"text": "Great start to the week!", "date": "2024-01-01"},
            {"text": "Feeling stressed about deadlines", "date": "2024-01-02"},
            {"text": "Regular day at work", "date": "2024-01-03"},
            {"text": "Accomplished so much today!", "date": "2024-01-04"},
        ]

        # Create wrapper instance for demo
        wrapper = SentimentAnalyzerWrapper()
        # Manually set up for demo (in production, load_context handles this)
        wrapper.pipeline = pipeline
        wrapper.label_encoder = label_encoder
        wrapper._label_map = dict(enumerate(label_encoder.classes_))
        wrapper.confidence_thresholds = {"high": 0.7, "medium": 0.5, "low": 0.3}

        trends = wrapper.analyze_sentiment_trends(sample_entries)
        print(f"Dominant sentiment: {trends['dominant_sentiment']}")
        print(f"Distribution: {trends['overall_distribution']}")

        print("\nSentiment model registered successfully!")
        print(f"Sentiment labels: {list(label_encoder.classes_)}")

        return wrapper


if __name__ == "__main__":
    train_and_register()
