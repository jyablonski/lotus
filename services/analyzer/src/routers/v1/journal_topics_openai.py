import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.clients.openai_topic_client import OpenAITopicClient
from src.config import settings
from src.crud.journal_topics import create_or_update_topics, get_topics_by_journal_id
from src.crud.journals import get_journal_by_id
from src.dependencies import get_db, get_openai_topic_client
from src.schemas.openai_topics import AnalysisRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["topics"])


@router.post("/journals/{journal_id}/topics", status_code=status.HTTP_204_NO_CONTENT)
async def extract_journal_topics(
    journal_id: int,
    max_topics: int = 7,
    db: Session = Depends(get_db),
    topic_client: OpenAITopicClient = Depends(get_openai_topic_client),
):
    """Extract topics from a journal entry using OpenAI."""
    try:
        # Get the journal entry
        journal = get_journal_by_id(db, journal_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found")

        # Create analysis request
        request = AnalysisRequest(text=journal.journal_text, max_topics=max_topics)

        # Extract topics from the journal content
        analysis = await topic_client.analyze_topics(request)

        # Convert to format expected by your database layer
        topics = [
            {
                "topic_name": topic,
                "confidence": confidence,
                "ml_model_version": "openai-gpt-3.5-turbo",  # or settings.default_model
            }
            for topic, confidence in zip(analysis.topics, analysis.confidence_scores)
        ]

        # Store topics in database
        create_or_update_topics(db, journal_id, topics)

        logger.info(
            f"Extracted {len(topics)} topics for journal {journal_id} using OpenAI"
        )

    except Exception as e:
        logger.error(f"Error extracting topics for journal {journal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health/topics")
def topic_service_health(
    topic_client: OpenAITopicClient = Depends(get_openai_topic_client),
):
    """Health check endpoint for the OpenAI topic extraction service."""
    try:
        return {
            "status": "healthy",
            "service": "openai_topic_extraction",
            "model": settings.default_model,
        }
    except Exception as e:
        logger.error(f"Topic service health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "service": "openai_topic_extraction"},
        )
