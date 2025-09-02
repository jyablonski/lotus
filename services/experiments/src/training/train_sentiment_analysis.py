import pickle
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

from src.models.sentiment_analyzer import JournalSentimentAnalyzer


def get_training_data():
    """Get labeled training data for sentiment analysis"""
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
        {
            "text": "Did some household chores and organized my workspace.",
            "sentiment": "neutral",
        },
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


def train_and_register():
    """Train and register the sentiment analysis model"""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("journal_sentiment_analysis")

    # Get training data
    training_data = get_training_data()

    with mlflow.start_run():
        # Train model
        analyzer = JournalSentimentAnalyzer(model_version="1.0.0")

        # Split data for validation
        train_data, test_data = train_test_split(
            training_data,
            test_size=0.2,
            random_state=42,
            stratify=[item["sentiment"] for item in training_data],
        )

        analyzer.train(train_data)

        # Log parameters
        mlflow.log_param("model_version", "1.0.0")
        mlflow.log_param("training_samples", len(train_data))
        mlflow.log_param("test_samples", len(test_data))
        mlflow.log_param("sentiment_classes", len(analyzer.sentiment_labels))

        # Evaluate on test data
        test_texts = [item["text"] for item in test_data]
        test_labels = [item["sentiment"] for item in test_data]

        predictions = analyzer.predict_batch(test_texts)
        predicted_labels = [pred["sentiment"] for pred in predictions]
        confidences = [pred["confidence"] for pred in predictions]

        # Calculate accuracy
        accuracy = accuracy_score(test_labels, predicted_labels)
        avg_confidence = sum(confidences) / len(confidences)

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("avg_confidence", avg_confidence)

        print(f"Model Accuracy: {accuracy:.3f}")
        print(f"Average Confidence: {avg_confidence:.3f}")
        print("\nClassification Report:")
        print(classification_report(test_labels, predicted_labels))

        # Test with various examples
        test_cases = [
            "I feel amazing today! Everything is going perfectly.",
            "I'm worried about the future and feel overwhelmed.",
            "Had a normal day. Nothing special happened.",
            "Work was challenging but I learned a lot and feel proud of my progress.",
            "I hate everything about this situation and feel completely defeated.",
        ]

        print("\nTest Case Results:")
        for i, test_text in enumerate(test_cases, 1):
            result = analyzer.predict_sentiment(test_text)
            mlflow.log_metric(f"test_case_{i}_confidence", result["confidence"])
            print(
                f"{i}. '{test_text[:50]}...' -> {result['sentiment']} ({result['confidence']:.3f})"
            )

        # Create input example and signature for MLflow
        sample_input = ["Today was a good day"]
        sample_prediction = analyzer.predict_sentiment(sample_input[0])

        # Log the sklearn pipeline
        signature = infer_signature(sample_input, [sample_prediction])

        print("Starting Log Model")
        mlflow.sklearn.log_model(
            sk_model=analyzer.sentiment_pipeline,
            artifact_path="sentiment_model",
            registered_model_name="journal_sentiment_analyzer",
            signature=signature,
        )
        print("Finished Log Model")

        # Save the full analyzer with additional functionality
        with open("sentiment_analyzer.pkl", "wb") as f:
            pickle.dump(analyzer, f)
        mlflow.log_artifact("sentiment_analyzer.pkl")

        print(f"\nSentiment model v{analyzer.model_version} registered successfully!")
        print(f"Sentiment labels: {list(analyzer.sentiment_labels.values())}")

        # Demonstrate trend analysis capability
        sample_entries = [
            {"text": "Great start to the week!", "date": "2024-01-01"},
            {"text": "Feeling stressed about deadlines", "date": "2024-01-02"},
            {"text": "Regular day at work", "date": "2024-01-03"},
            {"text": "Accomplished so much today!", "date": "2024-01-04"},
        ]

        trends = analyzer.analyze_sentiment_trends(sample_entries)
        print("\nSample trend analysis:")
        print(f"Dominant sentiment: {trends['dominant_sentiment']}")
        print(f"Distribution: {trends['overall_distribution']}")

        return analyzer


if __name__ == "__main__":
    train_and_register()
