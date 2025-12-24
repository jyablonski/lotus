import logging

from sqlalchemy.orm import Session
from src.models.journal_details import JournalDetails

logger = logging.getLogger(__name__)


def create_or_update_analysis(db: Session, journal_id: int, analysis: dict) -> JournalDetails:
    """Insert or update journal analysis for a given journal ID."""
    logger.info(f"Starting analysis create/update for journal_id={journal_id}")

    try:
        existing = db.query(JournalDetails).filter_by(journal_id=journal_id).first()
        if existing:
            logger.info(f"Updating existing JournalDetails for journal_id={journal_id}")
            existing.sentiment_score = analysis["sentiment_score"]
            existing.mood_label = analysis["mood_label"]
            existing.keywords = analysis.get("keywords")
            db.flush()
            return existing

        logger.info(f"Inserting new JournalDetails for journal_id={journal_id}")
        new_entry = JournalDetails(
            journal_id=journal_id,
            sentiment_score=analysis["sentiment_score"],
            mood_label=analysis["mood_label"],
            keywords=analysis.get("keywords"),
        )
        db.add(new_entry)
        db.flush()
        return new_entry

    except Exception as e:
        logger.error(
            f"Database error during create/update for journal_id={journal_id}: {e}",
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.commit()
