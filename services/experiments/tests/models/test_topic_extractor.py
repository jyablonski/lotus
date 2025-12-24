import pytest
from src.models.topic_extractor import AdaptiveJournalTopicExtractor


class TestAdaptiveJournalTopicExtractor:
    def test_model_initialization(self):
        """Test model initializes with correct parameters"""
        model = AdaptiveJournalTopicExtractor(n_topics=5, model_version="1.0.0")
        assert model.n_topics == 5
        assert model.model_version == "1.0.0"
        assert model.topic_pipeline is None
        assert model.topic_labels == {}

    def test_training_creates_pipeline(self, sample_training_data):
        """Test that training creates the necessary pipeline"""
        model = AdaptiveJournalTopicExtractor(n_topics=3)
        model.train(sample_training_data)

        assert model.topic_pipeline is not None
        assert "tfidf" in model.topic_pipeline.named_steps
        assert "lda" in model.topic_pipeline.named_steps
        assert len(model.topic_labels) == 3

    def test_extract_topics_requires_trained_model(self):
        """Test that topic extraction fails on untrained model"""
        model = AdaptiveJournalTopicExtractor()

        with pytest.raises(ValueError, match="Model not trained yet"):
            model.extract_topics_adaptive("test text")

    def test_adaptive_topic_count_short_entry(self, trained_model):
        """Test that short entries get fewer topics"""
        short_text = "Good day."  # 2 words
        topics = trained_model.extract_topics_adaptive(short_text)

        assert len(topics) <= 2  # Max 2 topics for short entries
        for topic in topics:
            assert topic["confidence"] >= 0.25  # Higher confidence threshold

    def test_adaptive_topic_count_medium_entry(self, trained_model):
        """Test that medium entries get moderate topic count"""
        medium_text = (
            "Today was productive at work but I felt stressed about the deadline."  # 13 words
        )
        topics = trained_model.extract_topics_adaptive(medium_text)

        assert len(topics) <= 4  # Max 4 topics for medium entries
        for topic in topics:
            assert topic["confidence"] >= 0.20

    def test_adaptive_topic_count_long_entry(self, trained_model):
        """Test that long entries can have more topics"""
        long_text = "Today started with anxiety about work presentation but it went well. Colleagues were supportive and feedback was positive. Later had dinner with family which made me grateful. Ended day with reading and reflection on personal growth journey."  # 39 words
        topics = trained_model.extract_topics_adaptive(long_text)

        assert len(topics) <= 6  # Max 6 topics for long entries
        for topic in topics:
            assert topic["confidence"] >= 0.15

    def test_topic_output_format(self, trained_model):
        """Test that topics have correct format"""
        topics = trained_model.extract_topics_adaptive("Test journal entry about work stress")

        for topic in topics:
            assert "topic_id" in topic
            assert "topic_name" in topic
            assert "confidence" in topic
            assert isinstance(topic["topic_id"], int)
            assert isinstance(topic["topic_name"], str)
            assert isinstance(topic["confidence"], float)
            assert 0.0 <= topic["confidence"] <= 1.0

    def test_topics_sorted_by_confidence(self, trained_model):
        """Test that topics are returned in descending confidence order"""
        topics = trained_model.extract_topics_adaptive("Work stress and family gratitude")

        if len(topics) > 1:
            confidences = [topic["confidence"] for topic in topics]
            assert confidences == sorted(confidences, reverse=True)

    def test_reproducible_results_with_same_seed(self, sample_training_data):
        """Test that same random seed produces same results"""
        text = "Today was a stressful day at work"

        model1 = AdaptiveJournalTopicExtractor(n_topics=3)
        model1.train(sample_training_data)
        topics1 = model1.extract_topics_adaptive(text)

        model2 = AdaptiveJournalTopicExtractor(n_topics=3)
        model2.train(sample_training_data)
        topics2 = model2.extract_topics_adaptive(text)

        # Should get same topic IDs and similar confidences
        assert len(topics1) == len(topics2)
        if topics1:  # If any topics returned
            assert topics1[0]["topic_id"] == topics2[0]["topic_id"]
            assert abs(topics1[0]["confidence"] - topics2[0]["confidence"]) < 0.01

    def test_empty_text_handling(self, trained_model):
        """Test behavior with empty or very short text"""
        empty_topics = trained_model.extract_topics_adaptive("")
        whitespace_topics = trained_model.extract_topics_adaptive("   ")

        assert isinstance(empty_topics, list)
        assert isinstance(whitespace_topics, list)
        # Might be empty lists, which is fine

    def test_topic_labels_generated(self, trained_model):
        """Test that human-readable topic labels are created"""
        assert len(trained_model.topic_labels) > 0

        for topic_id, label in trained_model.topic_labels.items():
            assert isinstance(topic_id, int)
            assert isinstance(label, str)
            assert len(label) > 0
            assert topic_id >= 0
            assert topic_id < trained_model.n_topics


# Performance and integration tests
class TestTopicExtractorPerformance:
    def test_inference_speed(self, trained_model):
        """Test that inference completes quickly"""
        import time

        text = "Today was a challenging day with work stress and personal achievements"

        start_time = time.time()
        topics = trained_model.extract_topics_adaptive(text)
        duration = time.time() - start_time

        assert duration < 1.0  # Should complete in under 1 second
        assert isinstance(topics, list)  # And still return valid results

    def test_memory_usage_reasonable(self, sample_training_data):
        """Test that model doesn't consume excessive memory"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        model = AdaptiveJournalTopicExtractor(n_topics=10)
        model.train(sample_training_data * 10)  # Larger dataset

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        assert memory_increase < 100  # Should use less than 100MB additional memory
