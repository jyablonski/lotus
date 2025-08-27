# experiments/tests/conftest.py

import pytest
from src.models.topic_extractor import AdaptiveJournalTopicExtractor


@pytest.fixture
def sample_training_data():
    """Sample journal entries for training models in tests"""
    return [
        "I had a great day at work today, very productive",
        "Feeling anxious about the upcoming presentation",
        "Spent quality time with family, feeling grateful",
        "Workout at the gym made me feel energized",
        "Struggling with motivation and focus today",
    ]


@pytest.fixture
def trained_model(sample_training_data):
    """A trained model instance for testing"""
    model = AdaptiveJournalTopicExtractor(n_topics=3, model_version="test_v1")
    model.train(sample_training_data)
    return model
