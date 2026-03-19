# experiments/tests/conftest.py

import pytest
from src.models.sentiment_analyzer import JournalSentimentAnalyzer


@pytest.fixture
def sentiment_training_data():
    """Sample labeled data for training sentiment models"""
    return [
        {"text": "I had an amazing day, everything went perfectly!", "sentiment": "positive"},
        {"text": "Feeling so grateful for my wonderful friends.", "sentiment": "positive"},
        {"text": "Great workout this morning, feeling energized!", "sentiment": "positive"},
        {"text": "I'm so stressed and anxious about everything.", "sentiment": "negative"},
        {"text": "Today was terrible, nothing went right.", "sentiment": "negative"},
        {"text": "Feeling overwhelmed and exhausted.", "sentiment": "negative"},
        {"text": "Just a regular day, nothing special happened.", "sentiment": "neutral"},
        {"text": "Went to the store and did some errands.", "sentiment": "neutral"},
        {"text": "The weather was okay today.", "sentiment": "neutral"},
    ]


@pytest.fixture
def trained_sentiment_model(sentiment_training_data):
    """A trained sentiment analyzer instance for testing"""
    model = JournalSentimentAnalyzer(model_version="test_v1")
    model.train(sentiment_training_data)
    return model
