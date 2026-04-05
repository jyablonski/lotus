from contextlib import suppress
from unittest.mock import Mock

from src import dependencies


def test_get_db_closes_session(monkeypatch):
    fake_session = Mock()
    monkeypatch.setattr(dependencies, "SessionLocal", Mock(return_value=fake_session))

    generator = dependencies.get_db()
    yielded = next(generator)

    assert yielded is fake_session

    with suppress(StopIteration):
        next(generator)

    fake_session.close.assert_called_once()


def test_get_topic_client_is_cached(monkeypatch):
    dependencies.get_topic_client.cache_clear()
    fake_client = Mock()
    constructor = Mock(return_value=fake_client)
    monkeypatch.setattr(dependencies, "TopicClient", constructor)

    first = dependencies.get_topic_client()
    second = dependencies.get_topic_client()

    assert first is fake_client
    assert second is fake_client
    constructor.assert_called_once()


def test_get_sentiment_client_is_cached(monkeypatch):
    dependencies.get_sentiment_client.cache_clear()
    fake_client = Mock()
    constructor = Mock(return_value=fake_client)
    monkeypatch.setattr(dependencies, "SentimentClient", constructor)

    first = dependencies.get_sentiment_client()
    second = dependencies.get_sentiment_client()

    assert first is fake_client
    assert second is fake_client
    constructor.assert_called_once()


def test_get_openai_topic_client_enables_autolog_and_is_cached(monkeypatch):
    dependencies.get_openai_topic_client.cache_clear()
    fake_client = Mock()
    constructor = Mock(return_value=fake_client)
    autolog = Mock()
    monkeypatch.setattr(dependencies, "OpenAITopicClient", constructor)
    monkeypatch.setattr(dependencies.mlflow, "openai", Mock(autolog=autolog))

    first = dependencies.get_openai_topic_client()
    second = dependencies.get_openai_topic_client()

    assert first is fake_client
    assert second is fake_client
    constructor.assert_called_once()
    autolog.assert_called_once()


def test_get_embedding_client_is_cached(monkeypatch):
    dependencies.get_embedding_client.cache_clear()
    fake_client = Mock()
    constructor = Mock(return_value=fake_client)
    monkeypatch.setattr(dependencies, "EmbeddingClient", constructor)

    first = dependencies.get_embedding_client()
    second = dependencies.get_embedding_client()

    assert first is fake_client
    assert second is fake_client
    constructor.assert_called_once()


def test_content_safety_dependencies_are_cached(monkeypatch):
    dependencies.get_content_safety_detector.cache_clear()
    dependencies.get_content_flag_analyzer.cache_clear()

    fake_detector = Mock()
    fake_analyzer = Mock()
    detector_constructor = Mock(return_value=fake_detector)
    analyzer_constructor = Mock(return_value=fake_analyzer)
    monkeypatch.setattr(dependencies, "RegexContentSafetyDetector", detector_constructor)
    monkeypatch.setattr(dependencies, "RuleBasedContentFlagAnalyzer", analyzer_constructor)

    first_detector = dependencies.get_content_safety_detector()
    second_detector = dependencies.get_content_safety_detector()
    first_analyzer = dependencies.get_content_flag_analyzer()
    second_analyzer = dependencies.get_content_flag_analyzer()

    assert first_detector is fake_detector
    assert second_detector is fake_detector
    assert first_analyzer is fake_analyzer
    assert second_analyzer is fake_analyzer
    detector_constructor.assert_called_once()
    analyzer_constructor.assert_called_once()
