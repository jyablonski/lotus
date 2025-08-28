from typing import Any

from sqlalchemy.orm import Session

from src.models.journal_topics import JournalTopics


def create_or_update_topics(db: Session, journal_id: int, topics: list[dict[str, Any]]):
    """Create or update topic analysis for a journal entry"""
    # Delete existing topics for this journal
    db.query(JournalTopics).filter(JournalTopics.journal_id == journal_id).delete()

    # Insert new topics
    topic_records = []
    for topic in topics:
        topic_record = JournalTopics(
            journal_id=journal_id,
            topic_name=topic["topic_name"],
            confidence=topic["confidence"],
            ml_model_version=topic.get("model_version", "unknown"),
        )
        topic_records.append(topic_record)

    db.add_all(topic_records)
    db.commit()

    return topic_records


def get_journal_topics(db: Session, journal_id: int) -> list[JournalTopics]:
    """Get all topics for a specific journal entry"""
    return db.query(JournalTopics).filter(JournalTopics.journal_id == journal_id).all()


def get_user_topic_trends(
    db: Session, user_id: str, limit: int = 100
) -> list[dict[str, Any]]:
    """Get topic trends for a user across their journal entries"""
    # This would join with journals table to filter by user_id
    # Implementation depends on your journal model structure
    pass
