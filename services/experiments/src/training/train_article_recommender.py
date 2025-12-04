"""
Article Recommendation System - Complete Example
This demonstrates building an ML-based recommendation system with dummy data.

Uses: pandas, scikit-learn, torch, and mlflow for experiment tracking
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score
import mlflow
import mlflow.pytorch
from typing import List, Tuple
import pickle

# Set random seed for reproducibility
np.random.seed(42)
torch.manual_seed(42)


class ArticleRecommenderNN(nn.Module):
    """PyTorch Neural Network for Article Recommendations"""

    def __init__(self, input_size, hidden_size, output_size):
        super(ArticleRecommenderNN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, output_size),
            nn.Sigmoid(),  # Multi-label classification
        )

    def forward(self, x):
        return self.network(x)


class ArticleRecommender:
    """Complete recommendation system with MLflow tracking"""

    def __init__(self, use_pytorch=True):
        self.use_pytorch = use_pytorch
        self.mlb_articles = MultiLabelBinarizer()
        self.mlb_topics = MultiLabelBinarizer()
        self.mlb_recommended = MultiLabelBinarizer()
        self.scaler = StandardScaler()
        self.model = None
        self.all_articles = []
        self.article_topic_map = {}
        self.user_favorite_topics = {}

    def generate_dummy_data(self, n_samples=1000) -> pd.DataFrame:
        """Generate realistic dummy data for training"""

        print("Generating dummy data...")

        # Define our article universe
        self.all_articles = [f"article_{i}" for i in range(1, 51)]  # 50 articles

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
        self.article_topic_map = {}
        for article in self.all_articles:
            n_topics = np.random.randint(1, 4)
            article_topics = np.random.choice(topics, n_topics, replace=False).tolist()
            self.article_topic_map[article] = article_topics

        # Generate training data
        data = []
        for i in range(n_samples):
            user_id = f"user_{i % 200}"  # 200 unique users

            # Generate user favorite topics (1-3 topics per user)
            if user_id not in self.user_favorite_topics:
                n_fav_topics = np.random.randint(1, 4)
                self.user_favorite_topics[user_id] = np.random.choice(
                    topics, n_fav_topics, replace=False
                ).tolist()

            favorite_topics = self.user_favorite_topics[user_id]

            # Generate articles read (2-8 articles)
            n_articles_read = np.random.randint(2, 9)
            articles_read = np.random.choice(
                self.all_articles, n_articles_read, replace=False
            ).tolist()

            # Time on site (in seconds) - correlated with number of articles
            time_on_site = n_articles_read * np.random.randint(60, 300)

            # Generate recommendations based on user preferences
            # This simulates the "forced" output based on logical rules
            recommended = self._generate_logical_recommendations(
                articles_read, favorite_topics
            )

            data.append(
                {
                    "user_id": user_id,
                    "article_ids_read": articles_read,
                    "time_on_site": time_on_site,
                    "favorite_topics": favorite_topics,
                    "recommended_article_ids": recommended,
                }
            )

        df = pd.DataFrame(data)
        print(f"Generated {len(df)} training samples")
        return df

    def _generate_logical_recommendations(
        self,
        articles_read: List[str],
        favorite_topics: List[str],
        n_recommendations: int = 5,
    ) -> List[str]:
        """Generate logical recommendations based on rules"""

        # Get topics from articles read
        read_topics = set()
        for article in articles_read:
            read_topics.update(self.article_topic_map[article])

        # Combine with favorite topics
        relevant_topics = read_topics.union(set(favorite_topics))

        # Find articles matching these topics that haven't been read
        candidates = []
        for article in self.all_articles:
            if article not in articles_read:
                article_topics = set(self.article_topic_map[article])
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
            remaining = [
                a
                for a in self.all_articles
                if a not in articles_read and a not in recommended
            ]
            recommended.extend(
                np.random.choice(
                    remaining,
                    min(n_recommendations - len(recommended), len(remaining)),
                    replace=False,
                ).tolist()
            )

        return recommended[:n_recommendations]

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Convert raw data into feature matrix and labels"""

        print("Preparing features...")

        # One-hot encode articles read
        articles_encoded = self.mlb_articles.fit_transform(df["article_ids_read"])

        # One-hot encode favorite topics
        topics_encoded = self.mlb_topics.fit_transform(df["favorite_topics"])

        # Normalize time on site
        time_normalized = self.scaler.fit_transform(df[["time_on_site"]].values)

        # Combine all features
        X = np.hstack([articles_encoded, topics_encoded, time_normalized])

        # Encode target (recommended articles)
        y = self.mlb_recommended.fit_transform(df["recommended_article_ids"])

        print(f"Feature shape: {X.shape}, Target shape: {y.shape}")
        return X, y

    def train_pytorch_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
    ):
        """Train PyTorch neural network with MLflow tracking"""

        print("\nTraining PyTorch model...")

        # Start MLflow run
        with mlflow.start_run(run_name="pytorch_recommender"):
            # Log parameters
            mlflow.log_param("model_type", "pytorch_nn")
            mlflow.log_param("epochs", epochs)
            mlflow.log_param("batch_size", batch_size)
            mlflow.log_param("learning_rate", learning_rate)

            input_size = X_train.shape[1]
            output_size = y_train.shape[1]
            hidden_size = 128

            # Initialize model
            self.model = ArticleRecommenderNN(input_size, hidden_size, output_size)
            criterion = nn.BCELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

            # Convert to tensors
            X_train_tensor = torch.FloatTensor(X_train)
            y_train_tensor = torch.FloatTensor(y_train)
            X_val_tensor = torch.FloatTensor(X_val)
            y_val_tensor = torch.FloatTensor(y_val)

            # Training loop
            for epoch in range(epochs):
                self.model.train()

                # Batch training
                for i in range(0, len(X_train_tensor), batch_size):
                    batch_X = X_train_tensor[i : i + batch_size]
                    batch_y = y_train_tensor[i : i + batch_size]

                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()

                # Validation
                if (epoch + 1) % 10 == 0:
                    self.model.eval()
                    with torch.no_grad():
                        val_outputs = self.model(X_val_tensor)
                        val_loss = criterion(val_outputs, y_val_tensor)

                        # Calculate metrics (using threshold of 0.5)
                        val_preds = (val_outputs > 0.5).numpy()
                        precision = precision_score(
                            y_val, val_preds, average="samples", zero_division=0
                        )
                        recall = recall_score(
                            y_val, val_preds, average="samples", zero_division=0
                        )
                        f1 = f1_score(
                            y_val, val_preds, average="samples", zero_division=0
                        )

                        print(
                            f"Epoch {epoch + 1}/{epochs} - "
                            f"Val Loss: {val_loss:.4f}, "
                            f"Precision: {precision:.4f}, "
                            f"Recall: {recall:.4f}, "
                            f"F1: {f1:.4f}"
                        )

                        mlflow.log_metric("val_loss", val_loss.item(), step=epoch)
                        mlflow.log_metric("precision", precision, step=epoch)
                        mlflow.log_metric("recall", recall, step=epoch)
                        mlflow.log_metric("f1_score", f1, step=epoch)

            # Log the model
            mlflow.pytorch.log_model(self.model, "model")

            print("Training complete!")

    def predict(
        self,
        user_id: str,
        article_ids_read: List[str],
        time_on_site: int,
        top_k: int = 5,
    ) -> List[str]:
        """Make predictions for a single user request"""

        # Get user's favorite topics
        favorite_topics = self.user_favorite_topics.get(
            user_id,
            ["tech"],  # Default if user not seen before
        )

        # Create feature vector
        articles_encoded = self.mlb_articles.transform([article_ids_read])
        topics_encoded = self.mlb_topics.transform([favorite_topics])
        time_normalized = self.scaler.transform([[time_on_site]])

        X = np.hstack([articles_encoded, topics_encoded, time_normalized])

        # Make prediction
        if self.use_pytorch and isinstance(self.model, ArticleRecommenderNN):
            self.model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X)
                predictions = self.model(X_tensor).numpy()[0]
        else:
            predictions = self.model.predict_proba(X)[0]

        # Get top K articles (excluding already read)
        article_scores = list(zip(self.mlb_recommended.classes_, predictions))
        article_scores.sort(key=lambda x: x[1], reverse=True)

        recommendations = []
        for article, score in article_scores:
            if article not in article_ids_read and len(recommendations) < top_k:
                recommendations.append(article)

        return recommendations

    def save_model(self, path: str = "/home/claude/recommender_model.pkl"):
        """Save the model and preprocessors"""
        model_data = {
            "model": self.model,
            "mlb_articles": self.mlb_articles,
            "mlb_topics": self.mlb_topics,
            "mlb_recommended": self.mlb_recommended,
            "scaler": self.scaler,
            "article_topic_map": self.article_topic_map,
            "user_favorite_topics": self.user_favorite_topics,
            "all_articles": self.all_articles,
            "use_pytorch": self.use_pytorch,
        }

        with open(path, "wb") as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {path}")

    @classmethod
    def load_model(cls, path: str = "/home/claude/recommender_model.pkl"):
        """Load a saved model"""
        with open(path, "rb") as f:
            model_data = pickle.load(f)

        recommender = cls(use_pytorch=model_data["use_pytorch"])
        recommender.model = model_data["model"]
        recommender.mlb_articles = model_data["mlb_articles"]
        recommender.mlb_topics = model_data["mlb_topics"]
        recommender.mlb_recommended = model_data["mlb_recommended"]
        recommender.scaler = model_data["scaler"]
        recommender.article_topic_map = model_data["article_topic_map"]
        recommender.user_favorite_topics = model_data["user_favorite_topics"]
        recommender.all_articles = model_data["all_articles"]

        return recommender


def main():
    """Main training and demonstration function"""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("article_recommendations")

    # Create recommender
    recommender = ArticleRecommender(use_pytorch=True)

    # Generate dummy data
    df = recommender.generate_dummy_data(n_samples=2000)

    # Prepare features
    X, y = recommender.prepare_features(df)

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    recommender.train_pytorch_model(
        X_train, y_train, X_val, y_val, epochs=50, batch_size=32, learning_rate=0.001
    )

    # Save model
    recommender.save_model()

    # Demo prediction
    print("\n" + "=" * 60)
    print("DEMO PREDICTION")
    print("=" * 60)

    example_user = "user_42"
    example_articles = ["article_5", "article_12", "article_23"]
    example_time = 450

    print("\nInput:")
    print(f"  User ID: {example_user}")
    print(f"  Articles Read: {example_articles}")
    print(f"  Time on Site: {example_time}s")
    print(
        f"  User Favorite Topics: {recommender.user_favorite_topics.get(example_user, 'N/A')}"
    )

    recommendations = recommender.predict(
        example_user, example_articles, example_time, top_k=5
    )

    print(f"\nRecommended Articles: {recommendations}")

    # Show what topics these recommendations cover
    print("\nRecommended Article Topics:")
    for article in recommendations:
        topics = recommender.article_topic_map.get(article, [])
        print(f"  {article}: {topics}")

    print("\n" + "=" * 60)
    print("Training complete! Model saved and ready for use.")
    print("=" * 60)


if __name__ == "__main__":
    main()
