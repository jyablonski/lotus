import pickle

import mlflow
from mlflow.models.signature import infer_signature
import mlflow.sklearn

from src.models.topic_extractor import AdaptiveJournalTopicExtractor


def get_training_data():
    """Get training data - you can enhance this to pull from your database later"""
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


def train_and_register():
    """Train and register the topic extraction model"""

    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("journal_topic_extraction")

    # Get training data
    training_texts = get_training_data()

    with mlflow.start_run():
        # Train model
        extractor = AdaptiveJournalTopicExtractor(n_topics=8, model_version="1.0.0")
        extractor.train(training_texts)

        # Log parameters
        mlflow.log_param("n_topics", 8)
        mlflow.log_param("model_version", "1.0.0")
        mlflow.log_param("training_samples", len(training_texts))

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

        for test_text, length_category in test_cases:
            topics = extractor.extract_topics_adaptive(test_text)
            mlflow.log_metric(f"topics_count_{length_category}", len(topics))
            print(
                f"{length_category.title()} entry ({len(test_text.split())} words): {len(topics)} topics"
            )
            for topic in topics:
                print(f"  - {topic['topic_name']}: {topic['confidence']:.3f}")

        # Create input example and signature
        sample_input = ["Today was a productive day at work"]

        # Get the pipeline's actual output (LDA topic probabilities)
        pipeline_output = extractor.topic_pipeline.transform(sample_input)

        signature = infer_signature(sample_input, pipeline_output)

        print("Starting Log Model")
        mlflow.sklearn.log_model(
            sk_model=extractor.topic_pipeline,
            name="topic_model",
            registered_model_name="adaptive_journal_topics",
            signature=signature,
            # input_example=sample_input,
        )
        print("Finished Log Model")

        # Also save the full extractor with topic labels
        with open("adaptive_extractor.pkl", "wb") as f:
            pickle.dump(extractor, f)
        mlflow.log_artifact("adaptive_extractor.pkl")

        print(f"\nModel v{extractor.model_version} registered successfully!")
        print(f"Topic labels discovered: {list(extractor.topic_labels.values())}")

        return extractor


if __name__ == "__main__":
    train_and_register()
