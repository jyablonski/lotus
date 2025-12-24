import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.clients.openai_topic_client import OpenAITopicClient
from src.config import settings
from src.crud.journal_topics import create_or_update_topics
from src.crud.journals import get_journal_by_id
from src.dependencies import get_db, get_openai_topic_client
from src.schemas.openai_topics import AnalysisRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/journals/{journal_id}/openai/topics", status_code=status.HTTP_204_NO_CONTENT)
async def extract_journal_topics(
    journal_id: int,
    max_topics: int = 7,
    db: Session = Depends(get_db),
    topic_client: OpenAITopicClient = Depends(get_openai_topic_client),
):
    """Extract topics from a journal entry using OpenAI."""
    # Get the journal entry
    journal = get_journal_by_id(db=db, journal_id=journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")

    try:
        # Create analysis request
        request = AnalysisRequest(text=journal.journal_text, max_topics=max_topics)

        # Extract topics from the journal content
        analysis = await topic_client.analyze_topics(request=request)

        # Convert to format expected by your database layer
        topics = [
            {
                "topic_name": topic,
                "confidence": confidence,
                "ml_model_version": settings.default_model,
            }
            for topic, confidence in zip(analysis.topics, analysis.confidence_scores, strict=False)
        ]

        # Store topics in database
        create_or_update_topics(db=db, journal_id=journal_id, topics=topics)

        logger.info(f"Extracted {len(topics)} topics for journal {journal_id} using OpenAI")

    except Exception as e:
        logger.error(f"Error extracting topics for journal {journal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.get("/health/openai/topics")
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
        ) from None
