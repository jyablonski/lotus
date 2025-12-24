import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.clients.ml_topic_client import TopicClient
from src.crud.journal_topics import create_or_update_topics, get_topics_by_journal_id
from src.crud.journals import get_journal_by_id
from src.dependencies import get_db, get_topic_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/journals/{journal_id}/topics", status_code=status.HTTP_204_NO_CONTENT)
def extract_journal_topics(
    journal_id: int,
    db: Session = Depends(get_db),
    topic_client: TopicClient = Depends(get_topic_client),
):
    """Extract topics from a journal entry."""
    try:
        # Get the journal entry
        journal = get_journal_by_id(db, journal_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found")

        # Check if topic client is ready
        if not topic_client.is_ready():
            raise HTTPException(status_code=503, detail="Topic extraction service unavailable")

        # Extract topics from the journal content (includes model version)
        topics = topic_client.extract_topics(journal.journal_text)

        # Store topics in database
        create_or_update_topics(db, journal_id, topics)

        logger.info(
            f"Extracted {len(topics)} topics for journal {journal_id} using version "
            f"{topic_client.model_version}"
        )

    except Exception as e:
        logger.error(f"Error extracting topics for journal {journal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/journals/{journal_id}/topics")
def get_journal_topics(
    journal_id: int,
    db: Session = Depends(get_db),
):
    """Get stored topics for a journal entry."""
    try:
        journal = get_journal_by_id(db, journal_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found")

        # Get stored topics from database
        topics = get_topics_by_journal_id(db, journal_id)

        return {
            "journal_id": journal_id,
            "topics": [
                {
                    "topic_name": topic.topic_name,
                    "confidence": float(topic.confidence),
                    "ml_model_version": topic.ml_model_version,
                    "created_at": topic.created_at,
                }
                for topic in topics
            ],
        }

    except Exception as e:
        logger.error(f"Error getting topics for journal {journal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/health/topics")
def topic_service_health(topic_client: TopicClient = Depends(get_topic_client)):
    """Health check endpoint for the topic extraction service."""
    if topic_client.is_ready():
        model_info = topic_client.get_model_info()
        return {"status": "healthy", "service": "topic_extraction", **model_info}
    raise HTTPException(
        status_code=503,
        detail={"status": "unhealthy", "service": "topic_extraction"},
    )
