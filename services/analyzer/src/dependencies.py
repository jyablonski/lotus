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
