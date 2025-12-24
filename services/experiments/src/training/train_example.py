import mlflow
import mlflow.pytorch
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


# step 1: load training data or generate dummy data
def load_data():
    # Load from database, CSV, API, etc.
    df = pd.read_csv("data.csv")
    return df


# Or generate synthetic data
def generate_dummy_data(n_samples=1000):
    data = []
    for _i in range(n_samples):
        # Create sample data
        data.append({...})
    return pd.DataFrame(data)


# step 2: Transform raw data into model-ready features
def prepare_features(df):
    # Encode categorical
    encoder = LabelEncoder()
    df["category_encoded"] = encoder.fit_transform(df["category"])

    # Scale numerical
    scaler = StandardScaler()
    df["value_scaled"] = scaler.fit_transform(df[["value"]])

    # Separate features (X) and target (y)
    X = df[["feature1", "feature2", ...]]
    y = df["target"]

    return X, y, encoder, scaler  # Save encoders for later!


# step 3: split up training and test data
def split_data(X, y):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_val, y_train, y_val


# step 4: train the model using training data
def train_model(X_train, y_train, X_val, y_val):
    # Start MLflow tracking
    with mlflow.start_run(run_name="my_experiment"):
        # Log parameters
        mlflow.log_param("model_type", "random_forest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)

        # Initialize and train model
        model = RandomForestClassifier(n_estimators=100, max_depth=10)
        model.fit(X_train, y_train)

        # Evaluate
        train_score = model.score(X_train, y_train)
        val_score = model.score(X_val, y_val)

        # Log metrics
        mlflow.log_metric("train_accuracy", train_score)
        mlflow.log_metric("val_accuracy", val_score)

        # Log model to MLflow
        mlflow.sklearn.log_model(model, "model")

        return model


def main():
    # 1. Setup MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("my_experiment_name")

    # 2. Load data
    df = load_data()

    # 3. Prepare features
    X, y, _encoder, _scaler = prepare_features(df)

    # 4. Split data
    X_train, X_val, y_train, y_val = split_data(X, y)

    # 5. Train model
    model = train_model(X_train, y_train, X_val, y_val)
    print(model)

    # missing step: validate initial training results
    # missing step: train on test data
    # missing step: validate test data results
    # missing step: log both training results and validation test results
    # missing step: log model to mlflow
    # and also: once this is deployed in production and serving actual requests,
    # how we do monitor all 3 of the training metrics, validation metrics, and production metrics?
    # can we do that in mlflow?

    # 6. Save preprocessors so they can be used in the downstream services (important!)
    # if you scale your training data when building the model, you should scale your
    # actual input data when the model runs in production
    with mlflow.start_run():
        mlflow.log_artifact("encoder.pkl")
        mlflow.log_artifact("scaler.pkl")

    print("Training complete!")


if __name__ == "__main__":
    main()
