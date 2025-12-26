# """
# Improved Sentiment Analysis Training - Using Pre-trained Transformers
# Uses Hugging Face transformers with MLflow pyfunc wrapper for production deployment.
# """

# disabled because it's expensive to run torch
# import os
# import pickle
# import tempfile
# from typing import Any

# import mlflow
# import mlflow.pyfunc
# import numpy as np
# import pandas as pd
# from sklearn.metrics import accuracy_score, classification_report
# from sklearn.model_selection import train_test_split
# import torch
# from transformers import (
#     pipeline as hf_pipeline,
# )


# class RobertaSentimentWrapper(mlflow.pyfunc.PythonModel):
#     """
#     Production wrapper for RoBERTa-based sentiment analysis that:
#     1. Loads the Hugging Face model and tokenizer on startup
#     2. Provides predict method for single/batch text classification
#     3. Returns formatted output with sentiment labels and confidence scores
#     """

#     def load_context(self, context):
#         """
#         Called once when model is loaded (e.g., server startup).
#         Load artifacts from MLflow.

#         Available in context.artifacts:
#             - "model_config": path to model configuration
#             - "label_mapping": path to label mapping file
#         """
#         # Load configuration
#         with open(context.artifacts["model_config"], "rb") as f:
#             config = pickle.load(f)

#         self.model_name = config["model_name"]
#         self.label_mapping = config["label_mapping"]

#         # Initialize the sentiment pipeline
#         device = 0 if torch.cuda.is_available() else -1
#         self.sentiment_pipeline = hf_pipeline(
#             "sentiment-analysis",
#             model=self.model_name,
#             tokenizer=self.model_name,
#             device=device,
#         )

#     def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
#         """
#         Predict sentiment for journal entries.

#         Args:
#             context: MLflow context (unused here, artifacts already loaded)
#             model_input: DataFrame with column:
#                 - text (required): The journal entry text

#         Returns:
#             List of prediction dicts, one per input row:
#             [{"sentiment": "positive", "confidence": 0.85, "raw_output": {...}}, ...]
#         """
#         if "text" not in model_input.columns:
#             raise ValueError("model_input must contain 'text' column")

#         texts = model_input["text"].tolist()
#         results = self.sentiment_pipeline(texts)

#         predictions = []
#         for result in results:
#             mapped_label = self.label_mapping.get(result["label"], result["label"].lower())
#             predictions.append(
#                 {
#                     "sentiment": mapped_label,
#                     "confidence": round(result["score"], 4),
#                     "raw_output": result,
#                 }
#             )

#         return predictions

#     def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
#         """Predict sentiment for multiple texts (convenience method)."""
#         df = pd.DataFrame({"text": texts})
#         return self.predict(None, df)

#     def analyze_sentiment_trends(self, entries: list[dict[str, str]]) -> dict[str, Any]:
#         """Analyze sentiment trends over time."""
#         texts = [entry["text"] for entry in entries]
#         predictions = self.predict_batch(texts)

#         # Add predictions to entries
#         for i, entry in enumerate(entries):
#             entry["predicted_sentiment"] = predictions[i]["sentiment"]
#             entry["confidence"] = predictions[i]["confidence"]

#         # Calculate statistics
#         sentiments = [pred["sentiment"] for pred in predictions]
#         confidences = [pred["confidence"] for pred in predictions]

#         sentiment_counts = pd.Series(sentiments).value_counts().to_dict()

#         return {
#             "entries_with_predictions": entries,
#             "dominant_sentiment": max(sentiment_counts, key=sentiment_counts.get),
#             "overall_distribution": sentiment_counts,
#             "average_confidence": round(np.mean(confidences), 4),
#             "confidence_by_sentiment": {
#                 sentiment: round(
#                     np.mean(
#                         [
#                             pred["confidence"]
#                             for pred in predictions
#                             if pred["sentiment"] == sentiment
#                         ]
#                     ),
#                     4,
#                 )
#                 for sentiment in set(sentiments)
#             },
#         }


# class EnsembleSentimentWrapper(mlflow.pyfunc.PythonModel):
#     """
#     Production wrapper for ensemble sentiment analysis that:
#     1. Combines multiple transformer models for better accuracy
#     2. Uses majority voting for final prediction
#     3. Includes emotion detection
#     """

#     def load_context(self, context):
#         """
#         Called once when model is loaded (e.g., server startup).
#         Load artifacts from MLflow.
#         """
#         with open(context.artifacts["ensemble_config"], "rb") as f:
#             config = pickle.load(f)

#         device = 0 if torch.cuda.is_available() else -1

#         self.models = {}
#         for model_key, model_name in config["models"].items():
#             if model_key != "emotion":
#                 self.models[model_key] = hf_pipeline(
#                     "sentiment-analysis",
#                     model=model_name,
#                     tokenizer=model_name,
#                     device=device,
#                 )
#             else:
#                 self.models[model_key] = hf_pipeline(
#                     "text-classification",
#                     model=model_name,
#                     device=device,
#                 )

#         self.label_mapping = config["label_mapping"]

#     def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
#         """
#         Ensemble prediction from multiple models.

#         Args:
#             context: MLflow context
#             model_input: DataFrame with 'text' column

#         Returns:
#             List of prediction dicts with combined results
#         """
#         if "text" not in model_input.columns:
#             raise ValueError("model_input must contain 'text' column")

#         texts = model_input["text"].tolist()
#         results = []

#         for text in texts:
#             result = self._predict_single(text)
#             results.append(result)

#         return results

#     def _predict_single(self, text: str) -> dict[str, Any]:
#         """Ensemble prediction for a single text."""
#         predictions = {}

#         # Get predictions from sentiment models
#         for name, model in self.models.items():
#             if name != "emotion":
#                 pred = model(text)[0]
#                 mapped_label = self.label_mapping.get(pred["label"], pred["label"].lower())
#                 predictions[name] = {
#                     "sentiment": mapped_label,
#                     "confidence": pred["score"],
#                 }

#         # Get emotion prediction
#         emotion_result = self.models["emotion"](text)[0]

#         # Combine predictions (majority voting)
#         from collections import Counter

#         sentiment_votes = [pred["sentiment"] for pred in predictions.values()]
#         confidence_scores = [pred["confidence"] for pred in predictions.values()]

#         vote_counts = Counter(sentiment_votes)
#         final_sentiment = vote_counts.most_common(1)[0][0]
#         avg_confidence = np.mean(confidence_scores)

#         return {
#             "sentiment": final_sentiment,
#             "confidence": round(float(avg_confidence), 4),
#             "individual_predictions": predictions,
#             "emotion": emotion_result["label"],
#             "emotion_confidence": round(emotion_result["score"], 4),
#         }


# def get_training_data():
#     """Enhanced training data with more examples."""
#     return [
#         {
#             "text": "Today was incredibly productive at work. Finished the quarterly report and got positive feedback from my manager.",
#             "sentiment": "positive",
#         },
#         {
#             "text": "Had a wonderful dinner with family. Grateful for these moments of connection and love.",
#             "sentiment": "positive",
#         },
#         {"text": "Got an A+ on my exam, I'm stoked I'll pass the class.", "sentiment": "positive"},
#         {
#             "text": "It wasn't the worst day ever, but definitely could have been better.",
#             "sentiment": "negative",
#         },
#         {
#             "text": "My dog died, this is the single worst thing that's ever happened to me.",
#             "sentiment": "negative",
#         },
#         {"text": "Lost the championship vs Ohio State, fuck those guys.", "sentiment": "negative"},
#         {
#             "text": "I'm cautiously optimistic about the new changes at work.",
#             "sentiment": "neutral",
#         },
#         {"text": "The weather is fine I guess, nothing special.", "sentiment": "neutral"},
#         {"text": "The meatloaf was alright, I don't know", "sentiment": "neutral"},
#     ]


# def train_and_register_improved():
#     """Train and register the improved sentiment analysis model."""

#     mlflow.set_tracking_uri("http://localhost:5000")
#     mlflow.set_experiment("improved_journal_sentiment_analysis")

#     training_data = get_training_data()
#     model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"

#     with mlflow.start_run(run_name="roberta_sentiment"):
#         # Initialize the model for evaluation
#         device = 0 if torch.cuda.is_available() else -1
#         sentiment_pipeline = hf_pipeline(
#             "sentiment-analysis",
#             model=model_name,
#             tokenizer=model_name,
#             device=device,
#         )

#         label_mapping = {
#             "LABEL_0": "negative",
#             "LABEL_1": "neutral",
#             "LABEL_2": "positive",
#             "NEGATIVE": "negative",
#             "NEUTRAL": "neutral",
#             "POSITIVE": "positive",
#         }

#         # Check class distribution
#         sentiment_counts = {}
#         for item in training_data:
#             sentiment = item["sentiment"]
#             sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

#         print(f"Sentiment distribution: {sentiment_counts}")
#         print(f"Total samples: {len(training_data)}")

#         # Calculate appropriate test size
#         total_samples = len(training_data)
#         num_classes = len(sentiment_counts)
#         min_class_size = min(sentiment_counts.values())

#         if total_samples < 15:
#             print("Dataset too small for train/test split. Using all data for testing.")
#             train_data = training_data
#             test_data = training_data
#         else:
#             test_size = max(0.3, num_classes / total_samples + 0.1)
#             test_size = min(test_size, 0.5)

#             use_stratify = min_class_size >= 2 and (total_samples * test_size) >= num_classes

#             if use_stratify:
#                 train_data, test_data = train_test_split(
#                     training_data,
#                     test_size=test_size,
#                     random_state=42,
#                     stratify=[item["sentiment"] for item in training_data],
#                 )
#             else:
#                 print("Warning: Using random split due to class distribution.")
#                 train_data, test_data = train_test_split(
#                     training_data,
#                     test_size=test_size,
#                     random_state=42,
#                 )

#         # Log parameters
#         mlflow.log_param("model_name", model_name)
#         mlflow.log_param("training_samples", len(train_data))
#         mlflow.log_param("test_samples", len(test_data))
#         mlflow.log_param("device", "GPU" if torch.cuda.is_available() else "CPU")

#         # Evaluate on test data
#         test_texts = [item["text"] for item in test_data]
#         test_labels = [item["sentiment"] for item in test_data]

#         results = sentiment_pipeline(test_texts)
#         predicted_labels = [label_mapping.get(r["label"], r["label"].lower()) for r in results]
#         confidences = [r["score"] for r in results]

#         # Calculate metrics
#         accuracy = accuracy_score(test_labels, predicted_labels)
#         avg_confidence = np.mean(confidences)

#         mlflow.log_metric("accuracy", accuracy)
#         mlflow.log_metric("avg_confidence", avg_confidence)

#         print(f"Model Accuracy: {accuracy:.3f}")
#         print(f"Average Confidence: {avg_confidence:.3f}")
#         print("\nClassification Report:")
#         print(classification_report(test_labels, predicted_labels))

#         # Test challenging cases
#         challenging_cases = [
#             "I feel amazing today! Everything is going perfectly.",
#             "I'm worried about the future and feel overwhelmed.",
#             "Had a normal day. Nothing special happened.",
#             "Not bad, not great, just okay I suppose.",
#             "I hate everything about this situation and feel completely defeated.",
#             "It's whatever, I don't really care anymore.",
#             "Could be worse, could be better.",
#         ]

#         print("\nChallenging Test Cases:")
#         for i, test_text in enumerate(challenging_cases, 1):
#             result = sentiment_pipeline(test_text)[0]
#             mapped_label = label_mapping.get(result["label"], result["label"].lower())
#             print(f"{i}. '{test_text}' -> {mapped_label} ({result['score']:.3f})")

#         # Save artifacts to temporary directory
#         with tempfile.TemporaryDirectory() as tmp_dir:
#             # Save model configuration
#             config = {
#                 "model_name": model_name,
#                 "label_mapping": label_mapping,
#             }
#             config_path = os.path.join(tmp_dir, "model_config.pkl")
#             with open(config_path, "wb") as f:
#                 pickle.dump(config, f)

#             artifact_paths = {
#                 "model_config": config_path,
#             }

#             # Log the complete model with wrapper
#             print("Logging model with pyfunc wrapper...")
#             mlflow.pyfunc.log_model(
#                 artifact_path="sentiment_analyzer",
#                 python_model=RobertaSentimentWrapper(),
#                 artifacts=artifact_paths,
#                 code_paths=[__file__],
#                 pip_requirements=[
#                     "pandas",
#                     "numpy",
#                     "transformers",
#                     "torch",
#                     "mlflow",
#                 ],
#                 registered_model_name="improved_journal_sentiment_analyzer",
#             )
#             print("Model logged successfully!")

#         print("\nImproved sentiment model registered successfully!")

#         return sentiment_pipeline


# def train_and_register_ensemble():
#     """Train and register the ensemble sentiment analysis model."""

#     mlflow.set_tracking_uri("http://localhost:5000")
#     mlflow.set_experiment("ensemble_journal_sentiment_analysis")

#     with mlflow.start_run(run_name="ensemble_sentiment"):
#         # Define ensemble models
#         ensemble_models = {
#             "roberta": "cardiffnlp/twitter-roberta-base-sentiment-latest",
#             "distilbert": "distilbert-base-uncased-finetuned-sst-2-english",
#             "emotion": "j-hartmann/emotion-english-distilroberta-base",
#         }

#         label_mapping = {
#             "LABEL_0": "negative",
#             "LABEL_1": "neutral",
#             "LABEL_2": "positive",
#             "NEGATIVE": "negative",
#             "NEUTRAL": "neutral",
#             "POSITIVE": "positive",
#             "positive": "positive",
#             "negative": "negative",
#         }

#         # Log parameters
#         mlflow.log_param("ensemble_models", list(ensemble_models.keys()))
#         mlflow.log_param("device", "GPU" if torch.cuda.is_available() else "CPU")

#         # Test the ensemble
#         test_cases = [
#             "I absolutely love this new opportunity!",
#             "I'm feeling quite anxious about tomorrow.",
#             "It was an okay day, nothing remarkable.",
#             "This is the worst thing that could happen to me.",
#             "I'm feeling mixed emotions about this change.",
#         ]

#         print("Testing Ensemble Model...")
#         device = 0 if torch.cuda.is_available() else -1

#         models = {}
#         for model_key, model_name in ensemble_models.items():
#             if model_key != "emotion":
#                 models[model_key] = hf_pipeline(
#                     "sentiment-analysis",
#                     model=model_name,
#                     tokenizer=model_name,
#                     device=device,
#                 )
#             else:
#                 models[model_key] = hf_pipeline(
#                     "text-classification",
#                     model=model_name,
#                     device=device,
#                 )

#         for text in test_cases:
#             predictions = {}
#             for name, model in models.items():
#                 if name != "emotion":
#                     pred = model(text)[0]
#                     mapped_label = label_mapping.get(pred["label"], pred["label"].lower())
#                     predictions[name] = {"sentiment": mapped_label, "confidence": pred["score"]}

#             emotion_result = models["emotion"](text)[0]

#             from collections import Counter

#             sentiment_votes = [pred["sentiment"] for pred in predictions.values()]
#             vote_counts = Counter(sentiment_votes)
#             final_sentiment = vote_counts.most_common(1)[0][0]

#             print(f"Text: '{text}'")
#             print(f"Final: {final_sentiment}")
#             print(f"Emotion: {emotion_result['label']} ({emotion_result['score']:.3f})")
#             print("---")

#         # Save artifacts
#         with tempfile.TemporaryDirectory() as tmp_dir:
#             config = {
#                 "models": ensemble_models,
#                 "label_mapping": label_mapping,
#             }
#             config_path = os.path.join(tmp_dir, "ensemble_config.pkl")
#             with open(config_path, "wb") as f:
#                 pickle.dump(config, f)

#             artifact_paths = {
#                 "ensemble_config": config_path,
#             }

#             mlflow.pyfunc.log_model(
#                 artifact_path="ensemble_sentiment",
#                 python_model=EnsembleSentimentWrapper(),
#                 artifacts=artifact_paths,
#                 code_paths=[__file__],
#                 pip_requirements=[
#                     "pandas",
#                     "numpy",
#                     "transformers",
#                     "torch",
#                     "mlflow",
#                 ],
#                 registered_model_name="ensemble_journal_sentiment_analyzer",
#             )

#         print("\nEnsemble model registered successfully!")


# if __name__ == "__main__":
#     # Train improved model
#     train_and_register_improved()

#     # Train ensemble
#     train_and_register_ensemble()

#     print("\nTo install required packages:")
#     print("pip install transformers torch mlflow scikit-learn pandas numpy")
