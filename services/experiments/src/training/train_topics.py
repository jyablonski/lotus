"""
Topic Extraction Training - Journal Entries
Uses sklearn Pipeline with TF-IDF and LDA, with MLflow pyfunc wrapper for production deployment.
"""

import os
import pickle
import tempfile
from typing import Any

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


class TopicExtractorWrapper(mlflow.pyfunc.PythonModel):
    """
    Production wrapper for topic extraction that:
    1. Loads the sklearn pipeline and topic labels on startup
    2. Provides predict method for extracting topics from text
    3. Returns formatted output with topic names and confidence scores
    4. Supports adaptive topic extraction based on text length
    """

    def load_context(self, context):
        """
        Called once when model is loaded (e.g., server startup).
        Load artifacts from MLflow.

        Available in context.artifacts:
            - "sklearn_pipeline": path to saved sklearn pipeline
            - "topic_labels": path to topic labels mapping
            - "model_config": path to model configuration
        """
        self.pipeline = mlflow.sklearn.load_model(context.artifacts["sklearn_pipeline"])

        # Load topic labels
        with open(context.artifacts["topic_labels"], "rb") as f:
            self.topic_labels = pickle.load(f)

        # Load configuration
        with open(context.artifacts["model_config"], "rb") as f:
            self.config = pickle.load(f)

        self.n_topics = self.config.get("n_topics", 10)

    def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
        """
        Extract topics from journal entries.

        Args:
            context: MLflow context (unused here, artifacts already loaded)
            model_input: DataFrame with column:
                - text (required): The journal entry text

        Returns:
            List of topic dicts, one per input row:
            [{"topics": [{"topic_id": 0, "topic_name": "work", "confidence": 0.45}, ...]}, ...]
        """
        if "text" not in model_input.columns:
            raise ValueError("model_input must contain 'text' column")

        texts = model_input["text"].tolist()
        results = []

        for text in texts:
            topics = self._extract_topics_adaptive(text)
            results.append({"topics": topics})

        return results

    def _extract_topics_adaptive(self, text: str) -> list[dict[str, Any]]:
        """Extract topics with adaptive count based on text characteristics."""
        word_count = len(text.split())

        # Adaptive thresholds
        if word_count < 20:  # Short entry
            min_confidence = 0.25
            max_topics = 2
        elif word_count < 50:  # Medium entry
            min_confidence = 0.20
            max_topics = 4
        else:  # Long entry
            min_confidence = 0.15
            max_topics = 6

        # Get topic probabilities using the pipeline
        topic_probs = self.pipeline.transform([text])[0]

        # Filter and sort topics
        topics = []
        for i, confidence in enumerate(topic_probs):
            if confidence > min_confidence:
                topics.append(
                    {
                        "topic_id": i,
                        "topic_name": self.topic_labels.get(i, f"topic_{i}"),
                        "confidence": round(float(confidence), 4),
                    }
                )

        # Sort by confidence and limit to max_topics
        topics.sort(key=lambda x: x["confidence"], reverse=True)
        return topics[:max_topics]

    def extract_all_topics(self, text: str) -> list[dict[str, Any]]:
        """Extract all topics without filtering (for analysis purposes)."""
        topic_probs = self.pipeline.transform([text])[0]

        topics = []
        for i, confidence in enumerate(topic_probs):
            topics.append(
                {
                    "topic_id": i,
                    "topic_name": self.topic_labels.get(i, f"topic_{i}"),
                    "confidence": round(float(confidence), 4),
                }
            )

        topics.sort(key=lambda x: x["confidence"], reverse=True)
        return topics


def get_training_data():
    """Get training data for topic extraction."""
    return [
        "Today was incredibly productive at work. Finished the quarterly report and got positive feedback from my manager.",
        "Feeling anxious about tomorrow's presentation. Spent the evening preparing but still worried.",
        "Had a wonderful dinner with family. Grateful for these moments of connection and love.",
        "Struggled with motivation today. Everything felt overwhelming and I couldn't focus on anything.",
        "Great workout at the gym this morning! Feel energized and accomplished.",
        "Spent a quiet evening reading and drinking tea. Sometimes simple pleasures are the best.",
        "Work stress is really getting to me. Need to find better ways to manage the pressure.",
        "Surprised myself by how well the meeting went. Felt confident and prepared.",
        "Missing my friends who live far away. Technology helps but it's not the same as being together.",
        "Learned something new about myself today through a difficult conversation.",
        "Beautiful weather inspired a long walk in nature. Feeling peaceful and refreshed.",
        "Frustrated with my sleep schedule. Need to be more disciplined about bedtime routines.",
        "Proud of finishing that challenging project. The hard work really paid off.",
        "Dealing with relationship conflicts is draining but necessary for growth.",
        "Simple morning routine of coffee and journaling sets a positive tone for the day.",
    ]


def build_topic_pipeline(n_topics: int = 8) -> Pipeline:
    """Build sklearn pipeline for topic extraction."""
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=200,
                    stop_words="english",
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                ),
            ),
            (
                "lda",
                LatentDirichletAllocation(
                    n_components=n_topics,
                    random_state=42,
                    max_iter=20,
                    learning_method="batch",
                    doc_topic_prior=0.1,
                    topic_word_prior=0.01,
                ),
            ),
        ]
    )
    return pipeline


def generate_topic_labels(pipeline: Pipeline, n_topics: int) -> dict[int, str]:
    """Generate human-readable labels for topics based on top words."""
    feature_names = pipeline["tfidf"].get_feature_names_out()
    lda_model = pipeline["lda"]

    # Common journal themes for better labeling
    theme_keywords = {
        "work": ["work", "job", "office", "meeting", "project", "boss", "colleague"],
        "relationships": ["family", "friend", "love", "partner", "relationship", "social"],
        "health": ["exercise", "gym", "tired", "sleep", "energy", "healthy", "workout"],
        "emotions": ["happy", "sad", "angry", "excited", "nervous", "calm", "peaceful"],
        "stress": ["stress", "anxious", "worry", "overwhelmed", "pressure", "tension"],
        "accomplishment": ["accomplished", "proud", "finished", "completed", "achieved"],
        "leisure": ["relax", "book", "movie", "music", "hobby", "fun", "enjoy"],
        "gratitude": ["grateful", "thankful", "blessed", "appreciate", "lucky"],
        "reflection": ["think", "realize", "understand", "learn", "reflect", "insight"],
        "daily_life": ["morning", "evening", "home", "routine", "day", "time"],
    }

    topic_labels = {}
    for topic_idx in range(n_topics):
        # Get top words for this topic
        topic_dist = lda_model.components_[topic_idx]
        top_word_indices = topic_dist.argsort()[-10:][::-1]
        top_words = [feature_names[idx] for idx in top_word_indices]

        # Try to match to known themes
        best_theme = "general"
        max_matches = 0

        for theme, keywords in theme_keywords.items():
            matches = len(set(top_words) & set(keywords))
            if matches > max_matches:
                max_matches = matches
                best_theme = theme

        # If no good match, use top 2 words
        if max_matches < 2:
            best_theme = f"{top_words[0]}_{top_words[1]}"

        topic_labels[topic_idx] = best_theme

    return topic_labels


def train_and_register():
    """Train and register the topic extraction model."""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("journal_topic_extraction")

    # Get training data
    training_texts = get_training_data()
    n_topics = 8

    with mlflow.start_run(run_name="topic_extractor"):
        # Build and train pipeline
        pipeline = build_topic_pipeline(n_topics=n_topics)
        pipeline.fit(training_texts)

        # Generate topic labels
        topic_labels = generate_topic_labels(pipeline, n_topics)

        # Log parameters
        mlflow.log_param("n_topics", n_topics)
        mlflow.log_param("model_version", "1.0.0")
        mlflow.log_param("training_samples", len(training_texts))
        mlflow.log_param("max_features", 200)

        # Test the model
        test_cases = [
            ("Had a good day.", "short"),
            (
                "Work was stressful but I managed to complete my tasks and felt accomplished.",
                "medium",
            ),
            (
                "Today started with anxiety about the presentation, but it went better than expected. My colleagues were supportive and the feedback was positive. Later, I had dinner with family which always makes me feel grateful. Ended the day with some reading and reflection on how much I've grown this year.",
                "long",
            ),
        ]

        print("\nTest Results:")
        for test_text, length_category in test_cases:
            topic_probs = pipeline.transform([test_text])[0]

            # Apply adaptive thresholds
            word_count = len(test_text.split())
            if word_count < 20:
                min_confidence = 0.25
                max_topics = 2
            elif word_count < 50:
                min_confidence = 0.20
                max_topics = 4
            else:
                min_confidence = 0.15
                max_topics = 6

            topics = []
            for i, confidence in enumerate(topic_probs):
                if confidence > min_confidence:
                    topics.append(
                        {
                            "topic_id": i,
                            "topic_name": topic_labels.get(i, f"topic_{i}"),
                            "confidence": round(float(confidence), 4),
                        }
                    )

            topics.sort(key=lambda x: x["confidence"], reverse=True)
            topics = topics[:max_topics]

            mlflow.log_metric(f"topics_count_{length_category}", len(topics))
            print(
                f"{length_category.title()} entry ({len(test_text.split())} words): {len(topics)} topics"
            )
            for topic in topics:
                print(f"  - {topic['topic_name']}: {topic['confidence']:.3f}")

        # Save artifacts to temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save the sklearn pipeline
            sklearn_path = os.path.join(tmp_dir, "sklearn_pipeline")
            mlflow.sklearn.save_model(pipeline, sklearn_path)

            # Save topic labels
            topic_labels_path = os.path.join(tmp_dir, "topic_labels.pkl")
            with open(topic_labels_path, "wb") as f:
                pickle.dump(topic_labels, f)

            # Save model configuration
            config = {
                "n_topics": n_topics,
                "model_version": "1.0.0",
            }
            config_path = os.path.join(tmp_dir, "model_config.pkl")
            with open(config_path, "wb") as f:
                pickle.dump(config, f)

            # Define artifact paths for the wrapper
            artifact_paths = {
                "sklearn_pipeline": sklearn_path,
                "topic_labels": topic_labels_path,
                "model_config": config_path,
            }

            # Log the complete model with wrapper
            print("\nLogging model with pyfunc wrapper...")
            mlflow.pyfunc.log_model(
                artifact_path="topic_model",
                python_model=TopicExtractorWrapper(),
                artifacts=artifact_paths,
                code_paths=[__file__],
                pip_requirements=[
                    "pandas",
                    "numpy",
                    "scikit-learn",
                    "mlflow",
                ],
                registered_model_name="adaptive_journal_topics",
            )
            print("Model logged successfully!")

        print("\nModel v1.0.0 registered successfully!")
        print(f"Topic labels discovered: {list(topic_labels.values())}")

        return pipeline, topic_labels


if __name__ == "__main__":
    train_and_register()
