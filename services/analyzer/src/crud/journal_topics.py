import logging
from typing import Any

from sqlalchemy.orm import Session

from src.models.journal_topics import JournalTopics

logger = logging.getLogger(__name__)


def create_or_update_topics(
    db: Session, journal_id: int, topics: list[dict[str, Any]]
) -> list[JournalTopics]:
    """Create or update topics for a journal entry."""
    try:
        # Delete existing topics for this journal
        db.query(JournalTopics).filter(JournalTopics.journal_id == journal_id).delete()

        # Create new topic records
        topic_records = []
        for topic in topics:
            topic_record = JournalTopics(
                journal_id=journal_id,
                topic_name=topic["topic_name"],
                confidence=float(topic["confidence"]),
                ml_model_version=topic["ml_model_version"],
            )
            db.add(topic_record)
            topic_records.append(topic_record)

        db.commit()
        logger.info(
            f"Created {len(topic_records)} topic records for journal {journal_id}"
        )
        return topic_records

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating topics for journal {journal_id}: {e}")
        raise


def get_topics_by_journal_id(db: Session, journal_id: int) -> list[JournalTopics]:
    """Get all topics for a journal entry."""
    return db.query(JournalTopics).filter(JournalTopics.journal_id == journal_id).all()


def get_topics_by_model_version(db: Session, model_version: str) -> list[JournalTopics]:
    """Get all topics created with a specific model version."""
    return (
        db.query(JournalTopics)
        .filter(JournalTopics.ml_model_version == model_version)
        .all()
    )
