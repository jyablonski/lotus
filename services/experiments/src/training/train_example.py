"""
Example Training Script - Template for ML Models
Demonstrates the pattern for training models with sklearn Pipeline/ColumnTransformer
and MLflow pyfunc wrapper for production deployment.
"""

import os
import pickle
import tempfile

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler


class ExampleModelWrapper(mlflow.pyfunc.PythonModel):
    """
    Production wrapper for example model that:
    1. Loads the sklearn pipeline and encoders on startup
    2. Provides predict and predict_proba methods for classification
    3. Returns formatted output for API consumption
    """

    def load_context(self, context):
        """
        Called once when model is loaded (e.g., server startup).
        Load artifacts from MLflow.

        Available in context.artifacts:
            - "sklearn_pipeline": path to saved sklearn pipeline
            - "label_encoder": path to saved label encoder for target
            - "model_config": path to model configuration
        """
        self.pipeline = mlflow.sklearn.load_model(context.artifacts["sklearn_pipeline"])

        # Load label encoder for target variable
        with open(context.artifacts["label_encoder"], "rb") as f:
            self.label_encoder = pickle.load(f)

        # Load configuration
        with open(context.artifacts["model_config"], "rb") as f:
            self.config = pickle.load(f)

        self._feature_cols = self.config.get("feature_cols", [])

    def predict(self, context, model_input: pd.DataFrame) -> list[dict]:
        """
        Make predictions for input data.

        Args:
            context: MLflow context (unused here, artifacts already loaded)
            model_input: DataFrame with feature columns

        Returns:
            List of prediction dicts, one per input row:
            [{"prediction": "class_a", "confidence": 0.85, "probabilities": {...}}, ...]
        """
        # Ensure required columns are present
        missing_cols = set(self._feature_cols) - set(model_input.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Select only feature columns in expected order
        X = model_input[self._feature_cols]

        # Get predictions and probabilities
        predictions = self.pipeline.predict(X)
        probabilities = self.pipeline.predict_proba(X)

        results = []
        for i, pred in enumerate(predictions):
            # Decode the label
            pred_label = self.label_encoder.inverse_transform([pred])[0]

            # Get probability for each class
            proba_dict = {
                self.label_encoder.inverse_transform([j])[0]: round(float(prob), 4)
                for j, prob in enumerate(probabilities[i])
            }

            results.append(
                {
                    "prediction": pred_label,
                    "confidence": round(float(max(probabilities[i])), 4),
                    "probabilities": proba_dict,
                }
            )

        return results

    def predict_proba(self, context, model_input: pd.DataFrame) -> np.ndarray:
        """
        Get class probabilities for input data.

        Args:
            context: MLflow context
            model_input: DataFrame with feature columns

        Returns:
            Array of shape (n_samples, n_classes) with probabilities
        """
        X = model_input[self._feature_cols]
        return self.pipeline.predict_proba(X)


def generate_dummy_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate synthetic training data."""
    np.random.seed(42)

    data = {
        "numeric_feature_1": np.random.randn(n_samples),
        "numeric_feature_2": np.random.randn(n_samples) * 10 + 50,
        "category": np.random.choice(["A", "B", "C"], n_samples),
        "target": np.random.choice(["positive", "negative", "neutral"], n_samples),
    }

    # Make target somewhat correlated with features
    df = pd.DataFrame(data)
    df.loc[(df["numeric_feature_1"] > 0.5) & (df["category"] == "A"), "target"] = "positive"
    df.loc[(df["numeric_feature_1"] < -0.5) & (df["category"] == "C"), "target"] = "negative"

    return df


def build_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    """
    Build sklearn pipeline with ColumnTransformer for preprocessing.

    Args:
        numeric_features: List of numeric column names
        categorical_features: List of categorical column names

    Returns:
        Configured sklearn Pipeline
    """
    # Define preprocessing for different column types
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ],
        remainder="drop",
    )

    # Create the full pipeline
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            ),
        ]
    )

    return pipeline


def train_and_register():
    """Train and register the example model."""

    # Setup MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("example_experiment")

    # Generate or load data
    df = generate_dummy_data(n_samples=1000)

    # Define feature columns
    numeric_features = ["numeric_feature_1", "numeric_feature_2"]
    categorical_features = ["category"]
    feature_cols = numeric_features + categorical_features

    with mlflow.start_run(run_name="example_model"):
        # Prepare features and target
        X = df[feature_cols]
        y_raw = df["target"]

        # Encode target labels
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y_raw)

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Build and train pipeline
        pipeline = build_pipeline(numeric_features, categorical_features)
        pipeline.fit(X_train, y_train)

        # Log parameters
        mlflow.log_param("model_type", "random_forest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("training_samples", len(X_train))
        mlflow.log_param("validation_samples", len(X_val))

        # Evaluate
        train_score = pipeline.score(X_train, y_train)
        val_score = pipeline.score(X_val, y_val)

        # Log metrics
        mlflow.log_metric("train_accuracy", train_score)
        mlflow.log_metric("val_accuracy", val_score)

        print(f"Training Accuracy: {train_score:.4f}")
        print(f"Validation Accuracy: {val_score:.4f}")

        # Save artifacts to temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save the sklearn pipeline
            sklearn_path = os.path.join(tmp_dir, "sklearn_pipeline")
            mlflow.sklearn.save_model(pipeline, sklearn_path)

            # Save label encoder
            label_encoder_path = os.path.join(tmp_dir, "label_encoder.pkl")
            with open(label_encoder_path, "wb") as f:
                pickle.dump(label_encoder, f)

            # Save model configuration
            config = {
                "feature_cols": feature_cols,
                "numeric_features": numeric_features,
                "categorical_features": categorical_features,
                "target_classes": list(label_encoder.classes_),
            }
            config_path = os.path.join(tmp_dir, "model_config.pkl")
            with open(config_path, "wb") as f:
                pickle.dump(config, f)

            # Define artifact paths for the wrapper
            artifact_paths = {
                "sklearn_pipeline": sklearn_path,
                "label_encoder": label_encoder_path,
                "model_config": config_path,
            }

            # Log the complete model with wrapper
            print("\nLogging model with pyfunc wrapper...")
            mlflow.pyfunc.log_model(
                artifact_path="example_model",
                python_model=ExampleModelWrapper(),
                artifacts=artifact_paths,
                code_paths=[__file__],
                pip_requirements=[
                    "pandas",
                    "numpy",
                    "scikit-learn",
                    "mlflow",
                ],
                registered_model_name="example_classifier",
            )
            print("Model logged successfully!")

        # Demonstrate loading and using the model
        print("\n" + "=" * 60)
        print("DEMO: Loading and using the model")
        print("=" * 60)

        # Create sample input
        sample_input = pd.DataFrame(
            [
                {"numeric_feature_1": 0.8, "numeric_feature_2": 55.0, "category": "A"},
                {"numeric_feature_1": -0.8, "numeric_feature_2": 45.0, "category": "C"},
                {"numeric_feature_1": 0.0, "numeric_feature_2": 50.0, "category": "B"},
            ]
        )

        # Create wrapper instance for demo
        wrapper = ExampleModelWrapper()
        wrapper.pipeline = pipeline
        wrapper.label_encoder = label_encoder
        wrapper._feature_cols = feature_cols

        predictions = wrapper.predict(None, sample_input)
        print("\nSample Predictions:")
        for i, (_, row) in enumerate(sample_input.iterrows()):
            print(f"  Input: {dict(row)}")
            print(f"  Output: {predictions[i]}")
            print()

        print("Training complete!")
        return pipeline, wrapper


if __name__ == "__main__":
    train_and_register()
