from collections.abc import Generator
from functools import lru_cache
import logging

import mlflow
from sqlalchemy.orm import Session

from src.clients.ml_sentiment_client import SentimentClient
from src.clients.ml_topic_client import TopicClient
from src.clients.openai_topic_client import OpenAITopicClient
from src.database import SessionLocal

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session]:
    """FastAPI Dependency for Database Operations

    Used in Endpoints that require Database ops

    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# First request creates TopicClient and loads model, all subsequent requests reuse the
# same client. 1000 requests = 1 model load. Without `lru_cache`, each request would
# create a new TopicClient instance and load the model again, resulting in significant
# overhead.
@lru_cache
def get_topic_client() -> TopicClient:
    """Dependency to get the singleton TopicClient instance.

    Formatting this way enables clean FastAPI dependency injection

    Example:

    @router.post("/journals/{journal_id}/topics")
    def extract_topics(
        journal_id: int,
        topic_client: TopicClient = Depends(get_topic_client),
    ):
    """
    logger.info("Creating TopicClient instance")
    return TopicClient()


@lru_cache
def get_sentiment_client() -> SentimentClient:
    """Dependency to get the singleton SentimentClient instance.

    Formatting this way enables clean FastAPI dependency injection

    Example:

    @router.post("/journals/{journal_id}/sentiment")
    def analyze_sentiment(
        journal_id: int,
        sentiment_client: SentimentClient = Depends(get_sentiment_client),
    ):
        # Your endpoint logic here
        result = sentiment_client.predict_sentiment(entry_text)
        return result

    @router.post("/journals/sentiment/batch")
    def analyze_sentiment_batch(
        entries: List[str],
        sentiment_client: SentimentClient = Depends(get_sentiment_client),
    ):
        results = sentiment_client.predict_sentiment_batch(entries)
        return results
    """
    logger.info("Creating SentimentClient instance")
    return SentimentClient()


@lru_cache
def get_openai_topic_client() -> OpenAITopicClient:
    """Dependency to get the singleton OpenAI TopicClient instance.

    Formatting this way enables clean FastAPI dependency injection

    Example:

    @router.post("/journals/{journal_id}/topics")
    def extract_topics(
        journal_id: int,
        topic_client: OpenAITopicClient = Depends(get_openai_topic_client),
    ):
    """
    logger.info("Creating OpenAI TopicClient instance")
    mlflow.openai.autolog()
    return OpenAITopicClient()
