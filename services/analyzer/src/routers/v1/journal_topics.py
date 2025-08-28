import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.crud.journal_topics import create_or_update_topics
from src.crud.journals import get_journal_by_id
from src.dependencies import get_db
# from src.main import logger
from src.ml.topic_client import MLTopicClient

router = APIRouter()

# Initialize ML client (you might want to make this a dependency)
# ml_client = MLTopicClient()


@router.post("/journals/{journal_id}/topics", status_code=status.HTTP_204_NO_CONTENT)
def extract_journal_topics(
    journal_id: int,
    db: Session = Depends(get_db),
):
    """Extract and save topics from journal entry"""
    # Get the journal entry from database
    print(f"ROUTE HIT: journal_id={journal_id}")  # Use print for immediate visibility
    logging.info(f"Extracting topics for journal {journal_id}")

    journal = get_journal_by_id(db=db, journal_id=journal_id)
    print(f"JOURNAL RESULT: {journal}")

    if not journal:
        print("NO JOURNAL FOUND - returning 404")
        raise HTTPException(status_code=404, detail="Journal entry not found")
    logging.info(f"Extracting topics for journal {journal_id}")

    journal = get_journal_by_id(db=db, journal_id=journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    try:
        ml_client = MLTopicClient()  # Create fresh instance
        topics = ml_client.extract_topic_probabilities(journal.journal_text)
        # Process topics and save to DB
    except Exception as e:
        logging.error(f"ML analysis failed: {e}")
        raise HTTPException(
            status_code=503, detail="ML service temporarily unavailable"
        )

    try:
        create_or_update_topics(db=db, journal_id=journal_id, topics=topics)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save topic analysis: {str(e)}"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
