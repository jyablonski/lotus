import logging

from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace
from sqlalchemy.orm import Session

from src.clients.openai_topic_client import OpenAITopicClient
from src.crud.journal_topics import create_or_update_topics
from src.crud.journals import get_journal_by_id
from src.dependencies import get_db, get_openai_topic_client
from src.schemas.openai_topics import AnalysisRequest

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
router = APIRouter()


@router.post(
    "/journals/{journal_id}/topics/openai",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def extract_journal_topics_openai(
    journal_id: int,
    max_topics: int = 7,
    db: Session = Depends(get_db),
    topic_client: OpenAITopicClient = Depends(get_openai_topic_client),
):
    """Extract topics from a journal entry using the OpenAI model."""
    journal = get_journal_by_id(db, journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")

    with tracer.start_as_current_span("openai_topics.extract") as span:
        span.set_attribute("journal.id", journal_id)
        span.set_attribute("model", topic_client.model)
        span.set_attribute("max_topics", max_topics)

        request = AnalysisRequest(text=journal.journal_text, max_topics=max_topics)
        analysis = await topic_client.analyze_topics(request)

    topics = [
        {
            "topic_name": topic,
            "confidence": score,
            "ml_model_version": topic_client.model,
        }
        for topic, score in zip(analysis.topics, analysis.confidence_scores, strict=True)
    ]

    create_or_update_topics(db, journal_id, topics)

    logger.info("Extracted %d OpenAI topics for journal %d", len(topics), journal_id)


@router.get("/health/topics/openai")
def openai_topic_service_health():
    """Health check endpoint for the OpenAI topic extraction service."""
    return {"status": "healthy", "service": "topic_extraction_openai"}
