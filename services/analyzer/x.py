#!/usr/bin/env python3
"""
Script to create lightweight test models for testing.
Run this once to generate the test model files that your test fixtures will load.

IMPORTANT: Run this from your project root directory so imports work correctly.
"""

import pickle
import logging
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.pipeline import Pipeline

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test model paths
TEST_FIXTURES_DIR = Path("tests/fixtures/models")
SENTIMENT_MODEL_PATH = TEST_FIXTURES_DIR / "sentiment_test_model.pkl"
TOPIC_MODEL_PATH = TEST_FIXTURES_DIR / "topic_test_model.pkl"


def create_test_sentiment_model():
    """Create a lightweight sentiment analysis model for testing."""
    logger.info("Creating test sentiment model...")

    # Training data for test model (small but diverse)
    training_texts = [
        # Positive examples
        "Today was amazing and wonderful! I feel so happy and accomplished.",
        "Had a great day at work and feeling fantastic about everything.",
        "Absolutely love spending time with friends and family. So grateful!",
        "Perfect weather for a walk. Feeling energetic and positive.",
        "Accomplished all my goals today. Very satisfied and proud.",
        # Negative examples
        "Feeling terrible and overwhelmed by everything going wrong.",
        "Work was stressful and frustrating. Having a really bad day.",
        "Anxious and worried about the future. Everything seems difficult.",
        "Disappointed by the news. Feeling sad and unmotivated.",
        "Struggling with challenges and feeling quite pessimistic.",
        # Neutral examples
        "Had a regular day with some routine tasks and normal activities.",
        "Attended a meeting that was informative but not particularly exciting.",
        "Spent time reading and doing some household chores today.",
        "Weather was okay, neither particularly good nor bad.",
        "Completed some paperwork and organized my workspace.",
        # Mixed/uncertain examples
        "Work was challenging but I learned something new from it.",
        "The weather was cloudy but at least it didn't rain much.",
        "Meeting was long but covered some important topics eventually.",
        "Had mixed feelings about the decision that was made today.",
        "Results were neither clearly good nor clearly bad overall.",
    ]

    # Labels: 0=negative, 1=neutral, 2=positive
    training_labels = [
        2,
        2,
        2,
        2,
        2,  # positive
        0,
        0,
        0,
        0,
        0,  # negative
        1,
        1,
        1,
        1,
        1,  # neutral
        1,
        1,
        1,
        1,
        1,  # mixed/uncertain -> neutral
    ]

    # Create pipeline (similar to your production model structure)
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=1000,  # Smaller than production
                    ngram_range=(1, 2),
                    stop_words="english",
                    lowercase=True,
                    min_df=1,  # Lower threshold for test data
                ),
            ),
            ("classifier", MultinomialNB(alpha=0.1)),
        ]
    )

    # Train the model
    pipeline.fit(training_texts, training_labels)

    # Test it works
    test_result = pipeline.predict_proba(["This is a happy test"])
    logger.info(f"Test prediction: {test_result}")

    # Save the model
    TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    with open(SENTIMENT_MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)

    logger.info(f"Test sentiment model saved to {SENTIMENT_MODEL_PATH}")


def create_test_topic_model():
    """Create a lightweight topic extraction model for testing."""
    logger.info("Creating test topic model...")

    # Training data for test model (representative of journal entries)
    training_texts = [
        # Work & Productivity
        "Had productive meetings at the office and finished important project deliverables.",
        "Busy day with deadlines but managed to complete all work tasks efficiently.",
        "Focused on work goals and made good progress on quarterly objectives.",
        # Emotional State
        "Feeling anxious about upcoming presentation but trying to stay positive.",
        "Happy and grateful for all the good things happening in life.",
        "Stressed about various challenges but working through them step by step.",
        # Daily Activities
        "Went grocery shopping and prepared meals for the week ahead.",
        "Cleaned the house and organized personal belongings around the home.",
        "Took a walk in the neighborhood and enjoyed the fresh air.",
        # Evening Reflection
        "Spent quiet evening reading books and reflecting on the day.",
        "Relaxed with tea while thinking about plans for tomorrow.",
        "Peaceful night doing journaling and meditation before bed.",
        # Morning Routine
        "Started day with coffee and planning out tasks and priorities.",
        "Morning workout gave me energy and positive mindset for day.",
        "Good breakfast and morning routine set tone for productive day.",
        # Feelings & Emotions
        "Love spending quality time with family and close friends.",
        "Grateful for supportive relationships and meaningful connections with others.",
        "Feeling content and satisfied with current life situation overall.",
    ]

    # Create pipeline (similar to your production model structure)
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=500,  # Smaller for test model
                    ngram_range=(1, 2),
                    stop_words="english",
                    lowercase=True,
                    min_df=1,
                    max_df=0.95,
                ),
            ),
            (
                "lda",
                LatentDirichletAllocation(
                    n_components=8,  # Match your production model
                    random_state=42,
                    max_iter=50,  # Fewer iterations for speed
                    learning_method="batch",
                ),
            ),
        ]
    )

    # Train the model
    pipeline.fit(training_texts)

    # Test it works
    test_result = pipeline.transform(["Had a productive work day"])
    logger.info(f"Test topic probabilities: {test_result}")

    # Save the model
    with open(TOPIC_MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)

    logger.info(f"Test topic model saved to {TOPIC_MODEL_PATH}")


def main():
    """Create both test models."""
    logger.info("Creating test models for test fixtures...")

    try:
        create_test_sentiment_model()
        create_test_topic_model()

        logger.info("✅ All test models created successfully!")
        logger.info(f"Sentiment model: {SENTIMENT_MODEL_PATH}")
        logger.info(f"Topic model: {TOPIC_MODEL_PATH}")
        logger.info("\nYou can now run your tests with real model fixtures.")

    except Exception as e:
        logger.error(f"❌ Failed to create test models: {e}")
        raise


if __name__ == "__main__":
    main()
