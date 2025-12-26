"""
Topic Extractor Model
Extracts topics from journal entries using LDA (Latent Dirichlet Allocation).
Uses sklearn Pipeline with TF-IDF vectorizer and LDA.
"""

from typing import Any

import mlflow
import mlflow.sklearn
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


class AdaptiveJournalTopicExtractor:
    """
    Topic extractor that adapts the number of extracted topics based on text length.
    Uses TF-IDF + LDA pipeline for topic modeling.
    """

    def __init__(self, n_topics: int = 10, model_version: str = "1.0.0"):
        self.n_topics = n_topics
        self.model_version = model_version
        self.topic_pipeline = None
        self.topic_labels = {}  # Map topic indices to human-readable names

    def train(self, texts: list[str]):
        """Train the topic extraction model."""
        # Create pipeline optimized for journal entries
        # Note: For text-only input, we use Pipeline directly.
        # ColumnTransformer would be used if we had mixed feature types.
        self.topic_pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=200,
                        stop_words="english",
                        lowercase=True,
                        ngram_range=(1, 2),
                        min_df=2,  # Word must appear in at least 2 documents
                        max_df=0.95,  # Ignore words in >95% of documents
                    ),
                ),
                (
                    "lda",
                    LatentDirichletAllocation(
                        n_components=self.n_topics,
                        random_state=42,
                        max_iter=20,
                        learning_method="batch",
                        doc_topic_prior=0.1,  # Lower alpha = fewer topics per document
                        topic_word_prior=0.01,  # Lower beta = fewer words per topic
                    ),
                ),
            ]
        )

        self.topic_pipeline.fit(texts)
        self._generate_topic_labels()
        return self

    def _generate_topic_labels(self):
        """Generate human-readable labels for topics based on top words."""
        if not self.topic_pipeline:
            return

        feature_names = self.topic_pipeline["tfidf"].get_feature_names_out()
        lda_model = self.topic_pipeline["lda"]

        # Common journal themes for better labeling
        theme_keywords = {
            "work": [
                "work",
                "job",
                "office",
                "meeting",
                "project",
                "boss",
                "colleague",
            ],
            "relationships": [
                "family",
                "friend",
                "love",
                "partner",
                "relationship",
                "social",
            ],
            "health": [
                "exercise",
                "gym",
                "tired",
                "sleep",
                "energy",
                "healthy",
                "workout",
            ],
            "emotions": [
                "happy",
                "sad",
                "angry",
                "excited",
                "nervous",
                "calm",
                "peaceful",
            ],
            "stress": [
                "stress",
                "anxious",
                "worry",
                "overwhelmed",
                "pressure",
                "tension",
            ],
            "accomplishment": [
                "accomplished",
                "proud",
                "finished",
                "completed",
                "achieved",
            ],
            "leisure": ["relax", "book", "movie", "music", "hobby", "fun", "enjoy"],
            "gratitude": ["grateful", "thankful", "blessed", "appreciate", "lucky"],
            "reflection": [
                "think",
                "realize",
                "understand",
                "learn",
                "reflect",
                "insight",
            ],
            "daily_life": ["morning", "evening", "home", "routine", "day", "time"],
        }

        for topic_idx in range(self.n_topics):
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

            self.topic_labels[topic_idx] = best_theme

    def extract_topics_adaptive(self, text: str) -> list[dict[str, Any]]:
        """Extract topics with adaptive count based on text characteristics."""
        if not self.topic_pipeline:
            raise ValueError("Model not trained yet")

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

        # Get topic probabilities
        text_tfidf = self.topic_pipeline["tfidf"].transform([text])
        topic_probs = self.topic_pipeline["lda"].transform(text_tfidf)[0]

        # Filter and sort topics
        topics = []
        for i, confidence in enumerate(topic_probs):
            if confidence > min_confidence:
                topics.append(
                    {
                        "topic_id": i,
                        "topic_name": self.topic_labels.get(i, f"topic_{i}"),
                        "confidence": float(confidence),
                    }
                )

        # Sort by confidence and limit to max_topics
        topics.sort(key=lambda x: x["confidence"], reverse=True)
        return topics[:max_topics]

    def extract_all_topics(self, text: str) -> list[dict[str, Any]]:
        """Extract all topics without filtering (for analysis purposes)."""
        if not self.topic_pipeline:
            raise ValueError("Model not trained yet")

        topic_probs = self.topic_pipeline.transform([text])[0]

        topics = []
        for i, confidence in enumerate(topic_probs):
            topics.append(
                {
                    "topic_id": i,
                    "topic_name": self.topic_labels.get(i, f"topic_{i}"),
                    "confidence": float(confidence),
                }
            )

        topics.sort(key=lambda x: x["confidence"], reverse=True)
        return topics


class TopicExtractorWithFeatures:
    """
    Extended topic extractor that handles mixed feature types.
    Uses ColumnTransformer for preprocessing different column types.
    """

    def __init__(self, n_topics: int = 10, model_version: str = "1.0.0"):
        self.n_topics = n_topics
        self.model_version = model_version
        self.pipeline = None
        self.topic_labels = {}

    def build_pipeline(
        self,
        text_column: str = "text",
        numeric_columns: list[str] | None = None,
        categorical_columns: list[str] | None = None,
    ) -> Pipeline:
        """
        Build a pipeline that handles text and optional numeric/categorical features.

        Args:
            text_column: Name of the text column
            numeric_columns: List of numeric column names
            categorical_columns: List of categorical column names

        Returns:
            Configured sklearn Pipeline
        """
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        transformers = [
            (
                "text",
                TfidfVectorizer(
                    max_features=200,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                ),
                text_column,
            ),
        ]

        if numeric_columns:
            transformers.append(("numeric", StandardScaler(), numeric_columns))

        if categorical_columns:
            transformers.append(
                ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_columns)
            )

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
        )

        self.pipeline = Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "lda",
                    LatentDirichletAllocation(
                        n_components=self.n_topics,
                        random_state=42,
                        max_iter=20,
                        learning_method="batch",
                    ),
                ),
            ]
        )

        return self.pipeline

    def train(self, df, text_column: str = "text"):
        """Train the model on a DataFrame."""
        if self.pipeline is None:
            self.build_pipeline(text_column=text_column)

        self.pipeline.fit(df)
        self._generate_topic_labels()

    def _generate_topic_labels(self):
        """Generate topic labels from the trained model."""
        # Access the text transformer from the ColumnTransformer
        preprocessor = self.pipeline.named_steps["preprocessor"]
        tfidf = preprocessor.named_transformers_["text"]
        lda_model = self.pipeline.named_steps["lda"]

        feature_names = tfidf.get_feature_names_out()

        for topic_idx in range(self.n_topics):
            topic_dist = lda_model.components_[topic_idx]
            top_word_indices = topic_dist.argsort()[-5:][::-1]
            top_words = [feature_names[idx] for idx in top_word_indices]
            self.topic_labels[topic_idx] = "_".join(top_words[:2])

    def transform(self, df) -> list[dict[str, Any]]:
        """Transform documents into topic distributions."""
        topic_distributions = self.pipeline.transform(df)

        results = []
        for topic_probs in topic_distributions:
            topics = []
            for i, confidence in enumerate(topic_probs):
                topics.append(
                    {
                        "topic_id": i,
                        "topic_name": self.topic_labels.get(i, f"topic_{i}"),
                        "confidence": float(confidence),
                    }
                )
            topics.sort(key=lambda x: x["confidence"], reverse=True)
            results.append({"topics": topics})

        return results


def train_and_register_model():
    """Train and register the adaptive topic model with MLflow."""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("journal_topic_extraction")

    # Enhanced training data with more variety
    training_texts = [
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

    with mlflow.start_run():
        # Train model
        extractor = AdaptiveJournalTopicExtractor(n_topics=8, model_version="1.0.0")
        extractor.train(training_texts)

        # Log parameters
        mlflow.log_param("n_topics", 8)
        mlflow.log_param("model_version", "1.0.0")
        mlflow.log_param("max_features", 200)
        mlflow.log_param("adaptive_thresholds", True)

        # Test on different entry lengths
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

        for test_text, length_category in test_cases:
            topics = extractor.extract_topics_adaptive(test_text)
            mlflow.log_metric(f"topics_count_{length_category}", len(topics))
            print(f"{length_category.title()} entry topics: {topics}")

        # Register model
        mlflow.sklearn.log_model(
            extractor.topic_pipeline,
            "topic_model",
            registered_model_name="adaptive_journal_topics",
        )

        # Log the full extractor for later use
        import pickle

        with open("adaptive_extractor.pkl", "wb") as f:
            pickle.dump(extractor, f)
        mlflow.log_artifact("adaptive_extractor.pkl")

        print(f"Model v{extractor.model_version} trained and registered successfully!")
        print(f"Topic labels: {extractor.topic_labels}")


if __name__ == "__main__":
    train_and_register_model()
