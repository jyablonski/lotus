import logging
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.ml.topic_client import TopicClient

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


@lru_cache
def get_topic_client() -> TopicClient:
    """Dependency to get the singleton TopicClient instance."""
    logger.info("Creating TopicClient instance")
    return TopicClient()
