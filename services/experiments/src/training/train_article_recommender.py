"""
Article Recommendation System - Complete Example
This demonstrates building an ML-based recommendation system with dummy data.

Uses: pandas, scikit-learn, and mlflow for experiment tracking
"""

import os
import tempfile

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Set random seed for reproducibility
np.random.seed(42)


class ArticleRecommenderWrapper(mlflow.pyfunc.PythonModel):
    """
    Production wrapper that:
    1. Loads user features and sklearn pipeline on startup
    2. Enriches incoming requests with user features (simulates feature store lookup)
    3. Runs predictions through the pipeline
    4. Formats output for API consumption
    """

    def load_context(self, context):
        """
        Called once when model is loaded (e.g., server startup).
        Load artifacts from MLflow.

        Available in context.artifacts:
            - "users_db": path to users parquet file
            - "articles_db": path to articles parquet file
            - "sklearn_pipeline": path to saved sklearn pipeline
        """
        self.users_df = pd.read_parquet(context.artifacts["users_db"])
        self.articles_df = pd.read_parquet(context.artifacts["articles_db"])
        self.article_topic_map = pd.read_parquet(context.artifacts["article_topic_map"])

        # all of the preprocessing and model steps were baked into this pipeline object,
        # stored when we called `pipeline.fit`, and then saved to MLflow.

        # now the API can load the model back in and use it for predictions on new data
        # using the those same steps
        self.pipeline = mlflow.sklearn.load_model(context.artifacts["sklearn_pipeline"])

        # Cache feature columns expected by pipeline
        self._user_feature_cols = ["favorite_topics"]
        self._session_feature_cols = ["time_on_site"]
        self._article_feature_cols = ["articles_read"]

    def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
        """
        Generate article recommendations for users.

        Args:
            context: MLflow context (unused here, artifacts already loaded)
            model_input: DataFrame with columns:
                - user_id (required)
                - articles_read (list of article ids read)
                - time_on_site (int)

        Returns:
            List of recommendation dicts, one per input row:
            [{"user_id": "user_123", "recommendations": [{"article_id": "article_1", "score": 0.85, ...}, ...]}, ...]
        """
        if "user_id" not in model_input.columns:
            raise ValueError("model_input must contain 'user_id' column")

        # Enrich with user features (simulates feature store lookup)
        enriched = model_input.merge(
            self.users_df[["user_id", "favorite_topics"]],
            on="user_id",
            how="left",
        )

        # Check for unknown users - use default topics for new users
        unknown_mask = enriched["favorite_topics"].isna()
        if unknown_mask.any():
            enriched.loc[unknown_mask, "favorite_topics"] = enriched.loc[
                unknown_mask, "favorite_topics"
            ].apply(lambda x: ["tech"])

        # Get probabilities for each article
        # The pipeline expects the raw features and handles all preprocessing
        probabilities = self.pipeline.predict_proba(enriched)

        # Format recommendations for each input row
        results = []
        for idx, row in enumerate(model_input.itertuples()):
            # Get probabilities for this row across all articles
            if isinstance(probabilities, list):
                # MultiOutputClassifier returns list of arrays
                row_probs = np.array(
                    [p[idx, 1] if p.shape[1] > 1 else p[idx, 0] for p in probabilities]
                )
            else:
                row_probs = probabilities[idx]

            recs = self._format_recommendations(
                row.user_id,
                row_probs,
                row.articles_read if hasattr(row, "articles_read") else [],
            )
            results.append(recs)

        return results

    def _format_recommendations(
        self, user_id: str, probabilities: np.ndarray, articles_read: list, top_k: int = 5
    ) -> dict:
        """
        Format raw probabilities into ranked recommendations.

        Args:
            user_id: The user ID
            probabilities: Array of click probabilities per article
            articles_read: List of articles already read by user
            top_k: Number of recommendations to return

        Returns:
            Dict with user_id and list of top_k recommendations sorted by score
        """
        # Get top k article indices by probability (descending)
        top_indices = np.argsort(probabilities)[::-1]

        recommendations = []
        for article_idx in top_indices:
            article_id = self.articles_df.iloc[article_idx]["article_id"]

            # Skip articles already read
            if article_id in articles_read:
                continue

            article_topics = (
                self.article_topic_map[self.article_topic_map["article_id"] == article_id][
                    "topics"
                ].iloc[0]
                if len(self.article_topic_map[self.article_topic_map["article_id"] == article_id])
                > 0
                else []
            )

            recommendations.append(
                {
                    "article_id": article_id,
                    "score": round(float(probabilities[article_idx]), 4),
                    "topics": article_topics,
                }
            )

            if len(recommendations) >= top_k:
                break

        return {
            "user_id": user_id,
            "recommendations": recommendations,
        }


def generate_dummy_data(
    n_samples: int = 1000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Generate realistic dummy data for training"""

    print("Generating dummy data...")

    # Define our article universe
    all_articles = [f"article_{i}" for i in range(1, 51)]  # 50 articles

    # Define topics
    topics = [
        "tech",
        "sports",
        "politics",
        "entertainment",
        "health",
        "science",
        "business",
        "travel",
        "food",
        "fashion",
    ]

    # Assign topics to articles (each article has 1-3 topics)
    article_topic_map = {}
    for article in all_articles:
        n_topics = np.random.randint(1, 4)
        article_topics = np.random.choice(topics, n_topics, replace=False).tolist()
        article_topic_map[article] = article_topics

    # Create articles dataframe
    articles_df = pd.DataFrame({"article_id": all_articles})

    # Create article topic map dataframe
    article_topic_df = pd.DataFrame(
        [{"article_id": k, "topics": v} for k, v in article_topic_map.items()]
    )

    # Generate user favorite topics
    user_favorite_topics = {}
    for i in range(200):
        user_id = f"user_{i}"
        n_fav_topics = np.random.randint(1, 4)
        user_favorite_topics[user_id] = np.random.choice(
            topics, n_fav_topics, replace=False
        ).tolist()

    # Create users dataframe
    users_df = pd.DataFrame(
        [{"user_id": k, "favorite_topics": v} for k, v in user_favorite_topics.items()]
    )

    # Generate training data
    data = []
    for i in range(n_samples):
        user_id = f"user_{i % 200}"  # 200 unique users
        favorite_topics = user_favorite_topics[user_id]

        # Generate articles read (2-8 articles)
        n_articles_read = np.random.randint(2, 9)
        articles_read = np.random.choice(all_articles, n_articles_read, replace=False).tolist()

        # Time on site (in seconds) - correlated with number of articles
        time_on_site = n_articles_read * np.random.randint(60, 300)

        # Generate recommendations based on user preferences
        recommended = _generate_logical_recommendations(
            articles_read, favorite_topics, all_articles, article_topic_map
        )

        data.append(
            {
                "user_id": user_id,
                "articles_read": articles_read,
                "time_on_site": time_on_site,
                "favorite_topics": favorite_topics,
                "recommended_articles": recommended,
            }
        )

    df = pd.DataFrame(data)
    print(f"Generated {len(df)} training samples")
    return df, users_df, articles_df, article_topic_df


def _generate_logical_recommendations(
    articles_read: list[str],
    favorite_topics: list[str],
    all_articles: list[str],
    article_topic_map: dict,
    n_recommendations: int = 5,
) -> list[str]:
    """Generate logical recommendations based on rules"""

    # Get topics from articles read
    read_topics = set()
    for article in articles_read:
        read_topics.update(article_topic_map[article])

    # Combine with favorite topics
    relevant_topics = read_topics.union(set(favorite_topics))

    # Find articles matching these topics that haven't been read
    candidates = []
    for article in all_articles:
        if article not in articles_read:
            article_topics = set(article_topic_map[article])
            # Score based on topic overlap
            overlap = len(article_topics.intersection(relevant_topics))
            if overlap > 0:
                candidates.append((article, overlap))

    # Sort by overlap and add some randomness
    candidates.sort(key=lambda x: x[1] + np.random.random() * 0.5, reverse=True)

    # Return top N
    recommended = [article for article, _ in candidates[:n_recommendations]]

    # Fill with random articles if needed
    if len(recommended) < n_recommendations:
        remaining = [a for a in all_articles if a not in articles_read and a not in recommended]
        recommended.extend(
            np.random.choice(
                remaining,
                min(n_recommendations - len(recommended), len(remaining)),
                replace=False,
            ).tolist()
        )

    return recommended[:n_recommendations]


def create_training_features(
    df: pd.DataFrame, all_articles: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create feature matrix and multi-label target for training.

    Returns:
        X: DataFrame with features
        y: DataFrame with binary columns for each article (multi-label target)
    """
    # Create features DataFrame
    X = df[["user_id", "articles_read", "time_on_site", "favorite_topics"]].copy()

    # Create multi-label target (binary indicator for each article)
    y_data = []
    for _, row in df.iterrows():
        article_indicators = {
            f"rec_{article}": 1 if article in row["recommended_articles"] else 0
            for article in all_articles
        }
        y_data.append(article_indicators)

    y = pd.DataFrame(y_data)

    return X, y


def build_pipeline(all_articles: list[str]) -> Pipeline:
    """
    Build sklearn pipeline with ColumnTransformer for preprocessing
    and MultiOutputClassifier for multi-label prediction.
    """
    # Define preprocessing for different column types
    # Note: articles_read and favorite_topics are lists, we need custom handling

    preprocessor = ColumnTransformer(
        transformers=[
            ("time_scaler", StandardScaler(), ["time_on_site"]),
            # For list columns, we'll handle them differently
            # Using passthrough for now and custom preprocessing
        ],
        remainder="drop",
    )

    # Create the full pipeline
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                MultiOutputClassifier(
                    RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
                ),
            ),
        ]
    )

    return pipeline


def prepare_features_for_pipeline(
    df: pd.DataFrame, all_articles: list[str], topics: list[str]
) -> pd.DataFrame:
    """
    Prepare features in a format suitable for the sklearn pipeline.
    Converts list columns to one-hot encoded columns.
    """
    result = df.copy()

    # One-hot encode articles_read
    for article in all_articles:
        result[f"read_{article}"] = result["articles_read"].apply(
            lambda x: 1 if article in x else 0
        )

    # One-hot encode favorite_topics
    for topic in topics:
        result[f"topic_{topic}"] = result["favorite_topics"].apply(lambda x: 1 if topic in x else 0)

    # Keep time_on_site as is
    # Drop original list columns
    result = result.drop(columns=["articles_read", "favorite_topics", "user_id"])

    return result


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
) -> Pipeline:
    """Train sklearn pipeline with MLflow tracking"""

    print("\nTraining model...")

    # Define feature columns
    feature_cols = [col for col in X_train.columns if col != "user_id"]

    # Build preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("scaler", StandardScaler(), ["time_on_site"]),
            (
                "passthrough",
                "passthrough",
                [col for col in feature_cols if col != "time_on_site"],
            ),
        ],
        remainder="drop",
    )

    # Full pipeline
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                MultiOutputClassifier(
                    RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
                ),
            ),
        ]
    )

    # Fit the pipeline
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_val)

    precision = precision_score(y_val, y_pred, average="samples", zero_division=0)
    recall = recall_score(y_val, y_pred, average="samples", zero_division=0)
    f1 = f1_score(y_val, y_pred, average="samples", zero_division=0)

    print("Validation Metrics:")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  F1: {f1:.4f}")

    return pipeline, {"precision": precision, "recall": recall, "f1": f1}


def main():
    """Main training and demonstration function"""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("article_recommendations")

    # Define topics
    topics = [
        "tech",
        "sports",
        "politics",
        "entertainment",
        "health",
        "science",
        "business",
        "travel",
        "food",
        "fashion",
    ]

    # Generate dummy data
    df, users_df, articles_df, article_topic_df = generate_dummy_data(n_samples=2000)
    all_articles = articles_df["article_id"].tolist()

    # Prepare features
    X, y = create_training_features(df, all_articles)

    # Convert list columns to one-hot encoded features
    X_prepared = prepare_features_for_pipeline(X, all_articles, topics)

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(X_prepared, y, test_size=0.2, random_state=42)

    # Start MLflow run
    with mlflow.start_run(run_name="sklearn_recommender"):
        # Log parameters
        mlflow.log_param("model_type", "random_forest_multioutput")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("n_articles", len(all_articles))

        # Train model
        pipeline, metrics = train_model(X_train, y_train, X_val, y_val)

        # Log metrics
        mlflow.log_metric("precision", metrics["precision"])
        mlflow.log_metric("recall", metrics["recall"])
        mlflow.log_metric("f1_score", metrics["f1"])

        # Save artifacts to temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save the sklearn pipeline
            sklearn_path = os.path.join(tmp_dir, "sklearn_pipeline")
            mlflow.sklearn.save_model(pipeline, sklearn_path)

            # Save user and article data as parquet
            users_path = os.path.join(tmp_dir, "users.parquet")
            articles_path = os.path.join(tmp_dir, "articles.parquet")
            article_topic_path = os.path.join(tmp_dir, "article_topic_map.parquet")

            users_df.to_parquet(users_path, index=False)
            articles_df.to_parquet(articles_path, index=False)
            article_topic_df.to_parquet(article_topic_path, index=False)

            # Define artifact paths for the wrapper
            artifact_paths = {
                "users_db": users_path,
                "articles_db": articles_path,
                "article_topic_map": article_topic_path,
                "sklearn_pipeline": sklearn_path,
            }

            # Log the complete model with wrapper
            mlflow.pyfunc.log_model(
                artifact_path="recommender_model",
                python_model=ArticleRecommenderWrapper(),
                artifacts=artifact_paths,
                code_paths=[__file__],
                pip_requirements=[
                    "pandas",
                    "numpy",
                    "scikit-learn",
                    "mlflow",
                    "pyarrow",
                ],
                registered_model_name="article_recommender",
            )

        print("Training complete! Model logged to MLflow.")

    # Demo prediction
    print("\n" + "=" * 60)
    print("DEMO PREDICTION")
    print("=" * 60)

    # Load the model back
    model_uri = "models:/article_recommender/latest"
    try:
        loaded_model = mlflow.pyfunc.load_model(model_uri)

        # Create sample input
        sample_input = pd.DataFrame(
            [
                {
                    "user_id": "user_42",
                    "articles_read": ["article_5", "article_12", "article_23"],
                    "time_on_site": 450,
                }
            ]
        )

        print("\nInput:")
        print("  User ID: user_42")
        print("  Articles Read: ['article_5', 'article_12', 'article_23']")
        print("  Time on Site: 450s")

        recommendations = loaded_model.predict(sample_input)
        print(f"\nRecommendations: {recommendations}")

    except Exception as e:
        print(f"Could not load model for demo (this is expected on first run): {e}")

    print("\n" + "=" * 60)
    print("Training complete! Model saved and ready for use.")
    print("=" * 60)


if __name__ == "__main__":
    main()
