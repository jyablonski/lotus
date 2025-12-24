import pickle
from typing import Any

import mlflow
from mlflow.models.signature import infer_signature
import mlflow.transformers
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline


class ImprovedJournalSentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Initialize with a pre-trained transformer model

        Popular options:
        - "cardiffnlp/twitter-roberta-base-sentiment-latest" (great for social media text)
        - "nlptown/bert-base-multilingual-uncased-sentiment" (supports multiple languages)
        - "j-hartmann/emotion-english-distilroberta-base" (emotion detection)
        - "microsoft/DialoGPT-medium" (conversational context)
        """
        self.model_name = model_name
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
        )

        # Load tokenizer for custom processing if needed
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

        # Map model outputs to your custom labels
        self.label_mapping = {
            "LABEL_0": "negative",  # Usually negative
            "LABEL_1": "neutral",  # Usually neutral
            "LABEL_2": "positive",  # Usually positive
            "NEGATIVE": "negative",
            "NEUTRAL": "neutral",
            "POSITIVE": "positive",
        }

    def predict_sentiment(self, text: str) -> dict[str, Any]:
        """Predict sentiment for a single text"""
        result = self.sentiment_pipeline(text)[0]

        # Map the label to your format
        mapped_label = self.label_mapping.get(result["label"], result["label"].lower())

        return {
            "sentiment": mapped_label,
            "confidence": result["score"],
            "raw_output": result,
        }

    def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Predict sentiment for multiple texts efficiently"""
        results = self.sentiment_pipeline(texts)

        predictions = []
        for result in results:
            mapped_label = self.label_mapping.get(result["label"], result["label"].lower())
            predictions.append(
                {
                    "sentiment": mapped_label,
                    "confidence": result["score"],
                    "raw_output": result,
                }
            )

        return predictions

    def analyze_sentiment_trends(self, entries: list[dict[str, str]]) -> dict[str, Any]:
        """Analyze sentiment trends over time"""
        texts = [entry["text"] for entry in entries]
        predictions = self.predict_batch(texts)

        # Add predictions to entries
        for i, entry in enumerate(entries):
            entry["predicted_sentiment"] = predictions[i]["sentiment"]
            entry["confidence"] = predictions[i]["confidence"]

        # Calculate statistics
        sentiments = [pred["sentiment"] for pred in predictions]
        confidences = [pred["confidence"] for pred in predictions]

        sentiment_counts = pd.Series(sentiments).value_counts()

        return {
            "entries_with_predictions": entries,
            "dominant_sentiment": sentiment_counts.index[0],
            "overall_distribution": sentiment_counts.to_dict(),
            "average_confidence": np.mean(confidences),
            "confidence_by_sentiment": {
                sentiment: np.mean(
                    [pred["confidence"] for pred in predictions if pred["sentiment"] == sentiment]
                )
                for sentiment in set(sentiments)
            },
        }


class EnsembleSentimentAnalyzer:
    """Combine multiple models for even better performance"""

    def __init__(self):
        self.models = {
            "roberta": ImprovedJournalSentimentAnalyzer(
                "cardiffnlp/twitter-roberta-base-sentiment-latest"
            ),
            "distilbert": ImprovedJournalSentimentAnalyzer(
                "distilbert-base-uncased-finetuned-sst-2-english"
            ),
            "emotion": pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
            ),
        }

    def predict_sentiment(self, text: str) -> dict[str, Any]:
        """Ensemble prediction from multiple models"""
        predictions = {}

        # Get predictions from main sentiment models
        for name, model in self.models.items():
            if name != "emotion":
                pred = model.predict_sentiment(text)
                predictions[name] = pred

        # Get emotion prediction
        emotion_result = self.models["emotion"](text)[0]

        # Combine predictions (simple voting)
        sentiment_votes = [pred["sentiment"] for pred in predictions.values()]
        confidence_scores = [pred["confidence"] for pred in predictions.values()]

        # Majority vote
        from collections import Counter

        vote_counts = Counter(sentiment_votes)
        final_sentiment = vote_counts.most_common(1)[0][0]

        # Average confidence
        avg_confidence = np.mean(confidence_scores)

        return {
            "sentiment": final_sentiment,
            "confidence": avg_confidence,
            "individual_predictions": predictions,
            "emotion": emotion_result["label"],
            "emotion_confidence": emotion_result["score"],
        }


def get_training_data():
    """Enhanced training data with more examples"""
    return [
        {
            "text": "Today was incredibly productive at work. Finished the quarterly report and got positive feedback from my manager.",
            "sentiment": "positive",
        },
        {
            "text": "Had a wonderful dinner with family. Grateful for these moments of connection and love.",
            "sentiment": "positive",
        },
        {
            "text": "Got an A+ on my exam, I'm stoked I'll pass the class.",
            "sentiment": "positive",
        },
        {
            "text": "It wasn't the worst day ever, but definitely could have been better.",
            "sentiment": "negative",
        },
        {
            "text": "My dog died, this is the single worst thing that's ever happened to me.",
            "sentiment": "negative",
        },
        {
            "text": "Lost the championship vs Ohio State, fuck those guys.",
            "sentiment": "negative",
        },
        {
            "text": "I'm cautiously optimistic about the new changes at work.",
            "sentiment": "neutral",
        },
        {
            "text": "The weather is fine I guess, nothing special.",
            "sentiment": "neutral",
        },
        {
            "text": "The meatloaf was alright, I don't know",
            "sentiment": "neutral",
        },
    ]


def train_and_register_improved():
    """Train and register the improved sentiment analysis model"""

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("improved_journal_sentiment_analysis")

    training_data = get_training_data()

    with mlflow.start_run():
        # Initialize improved analyzer
        analyzer = ImprovedJournalSentimentAnalyzer()

        # Check class distribution first
        sentiment_counts = {}
        for item in training_data:
            sentiment = item["sentiment"]
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        print(f"Sentiment distribution: {sentiment_counts}")
        print(f"Total samples: {len(training_data)}")

        # Calculate appropriate test size
        total_samples = len(training_data)
        num_classes = len(sentiment_counts)
        min_class_size = min(sentiment_counts.values())

        # Ensure test set has at least 1 sample per class, but adjust test_size if needed
        if total_samples < 15:  # Too small for meaningful split
            print("Dataset too small for train/test split. Using all data for testing.")
            train_data = training_data
            test_data = training_data  # Use same data for testing (not ideal but works for demo)
        else:
            # Use a larger test size to ensure we have enough samples per class
            test_size = max(
                0.3, num_classes / total_samples + 0.1
            )  # At least 30% or enough for stratification
            test_size = min(test_size, 0.5)  # But not more than 50%

            use_stratify = min_class_size >= 2 and (total_samples * test_size) >= num_classes

            if use_stratify:
                train_data, test_data = train_test_split(
                    training_data,
                    test_size=test_size,
                    random_state=42,
                    stratify=[item["sentiment"] for item in training_data],
                )
            else:
                print("Warning: Using random split due to class distribution.")
                train_data, test_data = train_test_split(
                    training_data,
                    test_size=test_size,
                    random_state=42,
                )

        # Log parameters
        mlflow.log_param("model_name", analyzer.model_name)
        mlflow.log_param("training_samples", len(train_data))
        mlflow.log_param("test_samples", len(test_data))
        mlflow.log_param("device", "GPU" if torch.cuda.is_available() else "CPU")

        # Evaluate on test data
        test_texts = [item["text"] for item in test_data]
        test_labels = [item["sentiment"] for item in test_data]

        predictions = analyzer.predict_batch(test_texts)
        predicted_labels = [pred["sentiment"] for pred in predictions]
        confidences = [pred["confidence"] for pred in predictions]

        # Calculate metrics
        accuracy = accuracy_score(test_labels, predicted_labels)
        avg_confidence = np.mean(confidences)

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("avg_confidence", avg_confidence)

        print(f"Model Accuracy: {accuracy:.3f}")
        print(f"Average Confidence: {avg_confidence:.3f}")
        print("\nClassification Report:")
        print(classification_report(test_labels, predicted_labels))

        # Test challenging cases
        challenging_cases = [
            "I feel amazing today! Everything is going perfectly.",
            "I'm worried about the future and feel overwhelmed.",
            "Had a normal day. Nothing special happened.",
            "Not bad, not great, just okay I suppose.",
            "I hate everything about this situation and feel completely defeated.",
            "It's whatever, I don't really care anymore.",
            "Could be worse, could be better.",
        ]

        print("\nChallenging Test Cases:")
        for i, test_text in enumerate(challenging_cases, 1):
            result = analyzer.predict_sentiment(test_text)
            print(f"{i}. '{test_text}' -> {result['sentiment']} ({result['confidence']:.3f})")

        # Create input example and signature for MLflow
        sample_input = [challenging_cases[0]]
        sample_prediction = analyzer.predict_sentiment(challenging_cases[0])
        signature = infer_signature(sample_input, [sample_prediction])
        print("Testing 1")

        # Log as pickle model instead of transformers (simpler approach)
        mlflow.sklearn.log_model(
            sk_model=analyzer,  # Log the whole analyzer object
            artifact_path="sentiment_analyzer",
            registered_model_name="improved_journal_sentiment_analyzer",
            signature=signature,
            pip_requirements=["transformers", "torch", "numpy", "pandas"],
        )

        print("Testing 123")
        # Save the analyzer
        with open("improved_sentiment_analyzer.pkl", "wb") as f:
            pickle.dump(analyzer, f)

        print("Testing 456")
        mlflow.log_artifact("improved_sentiment_analyzer.pkl")
        print("Testing 789")

        print("\nImproved sentiment model registered successfully!")

        return analyzer


def test_ensemble_model():
    """Test the ensemble approach"""
    print("Testing Ensemble Model...")
    ensemble = EnsembleSentimentAnalyzer()

    test_cases = [
        "I absolutely love this new opportunity!",
        "I'm feeling quite anxious about tomorrow.",
        "It was an okay day, nothing remarkable.",
        "This is the worst thing that could happen to me.",
        "I'm feeling mixed emotions about this change.",
    ]

    for text in test_cases:
        result = ensemble.predict_sentiment(text)
        print(f"Text: '{text}'")
        print(f"Final: {result['sentiment']} ({result['confidence']:.3f})")
        print(f"Emotion: {result['emotion']} ({result['emotion_confidence']:.3f})")
        print("---")


if __name__ == "__main__":
    # Train improved model
    improved_analyzer = train_and_register_improved()

    # Test ensemble
    test_ensemble_model()

    # Compare with original performance
    print("\nTo install required packages:")
    print("pip install transformers torch tensorflow mlflow scikit-learn pandas numpy")
