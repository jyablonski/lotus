import pytest
from src.models.sentiment_analyzer import JournalSentimentAnalyzer, SentimentAnalyzerWithFeatures


class TestJournalSentimentAnalyzer:
    def test_model_initialization(self):
        """Test model initializes with correct parameters"""
        model = JournalSentimentAnalyzer(model_version="1.0.0")
        assert model.model_version == "1.0.0"
        assert model.sentiment_pipeline is None
        assert model.sentiment_labels == {0: "negative", 1: "neutral", 2: "positive"}
        assert model.confidence_thresholds == {"high": 0.7, "medium": 0.5, "low": 0.3}

    def test_training_creates_pipeline(self, sentiment_training_data):
        """Test that training creates the necessary pipeline"""
        model = JournalSentimentAnalyzer()
        model.train(sentiment_training_data)

        assert model.sentiment_pipeline is not None
        assert "tfidf" in model.sentiment_pipeline.named_steps
        assert "classifier" in model.sentiment_pipeline.named_steps

    def test_predict_requires_trained_model(self):
        """Test that prediction fails on untrained model"""
        model = JournalSentimentAnalyzer()

        with pytest.raises(ValueError, match="Model must be trained before making predictions"):
            model.predict_sentiment("test text")

    def test_predict_sentiment_output_format(self, trained_sentiment_model):
        """Test that predictions have correct format"""
        result = trained_sentiment_model.predict_sentiment("I feel great today!")

        assert "sentiment" in result
        assert "confidence" in result
        assert "confidence_level" in result
        assert "all_scores" in result

        assert result["sentiment"] in ["positive", "negative", "neutral"]
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence_level"] in ["high", "medium", "low"]
        assert isinstance(result["all_scores"], dict)

    def test_predict_sentiment_all_scores_sum_to_one(self, trained_sentiment_model):
        """Test that all_scores probabilities sum to approximately 1"""
        result = trained_sentiment_model.predict_sentiment("Test journal entry")

        total = sum(result["all_scores"].values())
        assert abs(total - 1.0) < 0.01  # Allow small floating point error

    def test_predict_batch(self, trained_sentiment_model):
        """Test batch prediction works correctly"""
        texts = ["Great day!", "Terrible experience", "Nothing special"]
        results = trained_sentiment_model.predict_batch(texts)

        assert len(results) == 3
        for result in results:
            assert "sentiment" in result
            assert "confidence" in result

    def test_confidence_levels(self, trained_sentiment_model):
        """Test that confidence levels are assigned correctly based on thresholds"""
        # We can't guarantee specific confidence values, but we can check the logic
        result = trained_sentiment_model.predict_sentiment("I am so incredibly happy!")

        if result["confidence"] >= 0.7:
            assert result["confidence_level"] == "high"
        elif result["confidence"] >= 0.5:
            assert result["confidence_level"] == "medium"
        else:
            assert result["confidence_level"] == "low"

    def test_analyze_sentiment_trends(self, trained_sentiment_model):
        """Test sentiment trend analysis"""
        entries = [
            {"text": "Great start to the week!", "date": "2024-01-01"},
            {"text": "Feeling stressed about work", "date": "2024-01-02"},
            {"text": "Just a regular day", "date": "2024-01-03"},
        ]

        trends = trained_sentiment_model.analyze_sentiment_trends(entries)

        assert "individual_results" in trends
        assert "overall_distribution" in trends
        assert "average_confidence" in trends
        assert "dominant_sentiment" in trends
        assert "total_entries" in trends

        assert len(trends["individual_results"]) == 3
        assert trends["total_entries"] == 3
        assert trends["dominant_sentiment"] in ["positive", "negative", "neutral"]

    def test_analyze_sentiment_trends_includes_dates(self, trained_sentiment_model):
        """Test that trend analysis preserves dates"""
        entries = [
            {"text": "Happy day!", "date": "2024-01-01"},
            {"text": "Sad day!", "date": "2024-01-02"},
        ]

        trends = trained_sentiment_model.analyze_sentiment_trends(entries)

        for result in trends["individual_results"]:
            assert "date" in result

    def test_get_model_info_untrained(self):
        """Test model info for untrained model"""
        model = JournalSentimentAnalyzer()
        info = model.get_model_info()

        assert info["status"] == "not_trained"

    def test_get_model_info_trained(self, trained_sentiment_model):
        """Test model info for trained model"""
        info = trained_sentiment_model.get_model_info()

        assert info["status"] == "trained"
        assert info["model_version"] == "test_v1"
        assert "vocabulary_size" in info
        assert "sentiment_labels" in info
        assert "confidence_thresholds" in info
        assert info["vocabulary_size"] > 0

    def test_text_preprocessing(self):
        """Test that text preprocessing works correctly"""
        model = JournalSentimentAnalyzer()

        # Test lowercase conversion
        assert model._preprocess_text("HELLO WORLD") == "hello world"

        # Test whitespace normalization
        assert model._preprocess_text("hello   world") == "hello world"

        # Test stripping
        assert model._preprocess_text("  hello  ") == "hello"

    def test_empty_text_handling(self, trained_sentiment_model):
        """Test behavior with empty text"""
        result = trained_sentiment_model.predict_sentiment("")

        # Should still return a valid result structure
        assert "sentiment" in result
        assert "confidence" in result

    def test_reproducible_results(self, sentiment_training_data):
        """Test that same training data produces same predictions"""
        text = "I feel great today!"

        model1 = JournalSentimentAnalyzer()
        model1.train(sentiment_training_data)
        result1 = model1.predict_sentiment(text)

        model2 = JournalSentimentAnalyzer()
        model2.train(sentiment_training_data)
        result2 = model2.predict_sentiment(text)

        assert result1["sentiment"] == result2["sentiment"]
        assert abs(result1["confidence"] - result2["confidence"]) < 0.01


class TestSentimentAnalyzerWithFeatures:
    """Tests for the extended SentimentAnalyzerWithFeatures class"""

    def test_model_initialization(self):
        """Test model initializes with correct parameters"""
        model = SentimentAnalyzerWithFeatures(model_version="1.0.0")
        assert model.model_version == "1.0.0"
        assert model.pipeline is None
        assert model.sentiment_labels == {0: "negative", 1: "neutral", 2: "positive"}

    def test_build_pipeline_text_only(self):
        """Test building pipeline with text column only"""
        model = SentimentAnalyzerWithFeatures()
        pipeline = model.build_pipeline(text_column="text")

        assert pipeline is not None
        assert "preprocessor" in pipeline.named_steps
        assert "classifier" in pipeline.named_steps

    def test_build_pipeline_with_numeric_columns(self):
        """Test building pipeline with text and numeric columns"""
        model = SentimentAnalyzerWithFeatures()
        pipeline = model.build_pipeline(
            text_column="text",
            numeric_columns=["value1", "value2"],
        )

        assert pipeline is not None
        preprocessor = pipeline.named_steps["preprocessor"]
        transformer_names = [name for name, _, _ in preprocessor.transformers]
        assert "text" in transformer_names
        assert "numeric" in transformer_names

    def test_build_pipeline_with_categorical_columns(self):
        """Test building pipeline with text and categorical columns"""
        model = SentimentAnalyzerWithFeatures()
        pipeline = model.build_pipeline(
            text_column="text",
            categorical_columns=["category"],
        )

        assert pipeline is not None
        preprocessor = pipeline.named_steps["preprocessor"]
        transformer_names = [name for name, _, _ in preprocessor.transformers]
        assert "text" in transformer_names
        assert "categorical" in transformer_names

    def test_build_pipeline_with_all_column_types(self):
        """Test building pipeline with all column types"""
        model = SentimentAnalyzerWithFeatures()
        pipeline = model.build_pipeline(
            text_column="text",
            numeric_columns=["value"],
            categorical_columns=["category"],
        )

        assert pipeline is not None
        preprocessor = pipeline.named_steps["preprocessor"]
        transformer_names = [name for name, _, _ in preprocessor.transformers]
        assert "text" in transformer_names
        assert "numeric" in transformer_names
        assert "categorical" in transformer_names


class TestSentimentAnalyzerPerformance:
    """Performance tests for sentiment analyzer"""

    def test_inference_speed(self, trained_sentiment_model):
        """Test that inference completes quickly"""
        import time

        text = "Today was a wonderful day with great achievements and happy moments"

        start_time = time.time()
        result = trained_sentiment_model.predict_sentiment(text)
        duration = time.time() - start_time

        assert duration < 1.0  # Should complete in under 1 second
        assert "sentiment" in result

    def test_batch_inference_speed(self, trained_sentiment_model):
        """Test that batch inference is reasonably fast"""
        import time

        texts = ["Text number " + str(i) for i in range(100)]

        start_time = time.time()
        results = trained_sentiment_model.predict_batch(texts)
        duration = time.time() - start_time

        assert duration < 5.0  # 100 predictions in under 5 seconds
        assert len(results) == 100
