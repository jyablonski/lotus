import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.clients.ml_sentiment_client import SentimentClient
from src.crud.journal_sentiments import (
    create_or_update_sentiment,
    delete_sentiment,
    get_recent_sentiments,
    get_sentiment_by_journal_id,
    get_sentiment_stats,
    get_sentiment_trends,
    get_sentiments_by_journal_ids,
)
from src.dependencies import get_db, get_sentiment_client
from src.models.journals import Journals
from src.schemas.sentiments import (
    BulkSentimentAnalysisRequest,
    SentimentAnalysisRequest,
    SentimentDeleteResponse,
    SentimentResponse,
    SentimentStatsResponse,
    SentimentTrendResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/journals/{journal_id}/sentiment/analyze", response_model=SentimentResponse
)
def analyze_journal_sentiment(
    journal_id: int,
    request: SentimentAnalysisRequest,
    sentiment_client: SentimentClient = Depends(get_sentiment_client),
    db: Session = Depends(get_db),
):
    """Analyze sentiment for a journal entry and store the result (ID-only approach)"""

    journal = db.query(Journals).filter(Journals.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    try:
        analysis_result = sentiment_client.predict_sentiment(journal.journal_text)
    except Exception as e:
        logger.error(f"Sentiment analysis failed for journal {journal_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sentiment analysis failed: {str(e)}"
        )

    try:
        sentiment_record = create_or_update_sentiment(
            db=db,
            journal_id=journal_id,
            sentiment_data=analysis_result,
            force_update=request.force_reanalyze,
        )
        return sentiment_record
    except Exception as e:
        logger.error(f"Database operation failed for journal {journal_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database operation failed: {str(e)}"
        )


@router.get("/journals/{journal_id}/sentiment", response_model=SentimentResponse)
def get_journal_sentiment(
    journal_id: int,
    model_version: str | None = Query(
        None, description="Specific model version, defaults to latest"
    ),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis for a specific journal entry"""

    try:
        sentiment = get_sentiment_by_journal_id(
            db=db, journal_id=journal_id, model_version=model_version
        )

        if not sentiment:
            raise HTTPException(
                status_code=404,
                detail="Sentiment analysis not found for this journal entry",
            )

        return sentiment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve sentiment for journal {journal_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database operation failed: {str(e)}"
        )


@router.put("/journals/{journal_id}/sentiment", response_model=SentimentResponse)
def update_journal_sentiment(
    journal_id: int,
    request: SentimentAnalysisRequest,
    sentiment_client: SentimentClient = Depends(get_sentiment_client),
    db: Session = Depends(get_db),
):
    """Re-analyze and update sentiment for a journal entry"""

    # Force reanalyze when updating
    request.force_reanalyze = True
    return analyze_journal_sentiment(journal_id, request, sentiment_client, db)


@router.delete(
    "/journals/{journal_id}/sentiment", response_model=SentimentDeleteResponse
)
def delete_journal_sentiment(
    journal_id: int,
    model_version: str | None = Query(
        None, description="Specific model version to delete"
    ),
    db: Session = Depends(get_db),
):
    """Delete sentiment analysis for a journal entry"""

    try:

        deleted_count = delete_sentiment(
            db=db, journal_id=journal_id, model_version=model_version
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404, detail="No sentiment analysis found to delete"
            )

        return SentimentDeleteResponse(
            message=f"Deleted {deleted_count} sentiment analysis record(s)",
            journal_id=journal_id,
            deleted_count=deleted_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete sentiment for journal {journal_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete sentiment analysis: {str(e)}"
        )


@router.post(
    "/journals/sentiment/analyze-batch", response_model=list[SentimentResponse]
)
def analyze_journals_sentiment_batch(
    request: BulkSentimentAnalysisRequest,
    sentiment_client: SentimentClient = Depends(get_sentiment_client),
    db: Session = Depends(get_db),
):
    """Analyze sentiment for multiple journal entries"""

    # Fetch all journals
    journals = db.query(Journals).filter(Journals.id.in_(request.journal_ids)).all()
    found_ids = {j.id for j in journals}
    missing_ids = set(request.journal_ids) - found_ids

    if missing_ids:
        logger.warning(f"Journals not found: {missing_ids}")
        raise HTTPException(
            status_code=404, detail=f"Journal entries not found: {list(missing_ids)}"
        )

    results = []
    for journal in journals:
        try:
            # Run sentiment analysis
            analysis_result = sentiment_client.predict_sentiment(journal.journal_text)

            # Store result
            sentiment_record = create_or_update_sentiment(
                db=db,
                journal_id=journal.id,
                sentiment_data=analysis_result,
                force_update=request.force_reanalyze,
            )
            results.append(sentiment_record)

        except Exception as e:
            logger.error(f"Failed to analyze journal {journal.id}: {e}")
            # Continue with other journals, don't fail entire batch
            continue

    logger.info(
        f"Successfully analyzed {len(results)} out of {len(request.journal_ids)} journals"
    )
    return results


@router.get("/journals/sentiment/trends", response_model=list[SentimentTrendResponse])
def get_sentiment_trends_endpoint(
    user_id: int | None = Query(None, description="Filter by user ID"),
    days_back: int = Query(30, description="Number of days to look back", ge=1, le=365),
    group_by: str = Query("week", description="Group by: day, week, month"),
    reliable_only: bool = Query(True, description="Include only reliable predictions"),
    db: Session = Depends(get_db),
):
    """Get sentiment trends over time"""

    if group_by not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=400, detail="group_by must be 'day', 'week', or 'month'"
        )

    try:
        trends_data = get_sentiment_trends(
            db=db,
            days_back=days_back,
            group_by=group_by,
            reliable_only=reliable_only,
            user_id=user_id,
        )

        # Convert to Pydantic models
        trends = [
            SentimentTrendResponse(
                period=trend["period"],
                sentiment_counts=trend["sentiment_counts"],
                avg_confidence=trend["avg_confidence"],
                total_entries=trend["total_entries"],
                dominant_sentiment=trend["dominant_sentiment"],
            )
            for trend in trends_data
        ]

        return trends
    except Exception as e:
        logger.error(f"Failed to retrieve sentiment trends: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve sentiment trends: {str(e)}"
        )


@router.get("/journals/sentiment/stats", response_model=SentimentStatsResponse)
def get_sentiment_stats_endpoint(
    user_id: int | None = Query(None, description="Filter by user ID"),
    days_back: int | None = Query(None, description="Number of days to analyze", ge=1),
    db: Session = Depends(get_db),
):
    """Get overall sentiment analysis statistics"""

    try:
        stats = get_sentiment_stats(db=db, days_back=days_back, user_id=user_id)

        if stats["total_analyzed"] == 0:
            raise HTTPException(
                status_code=404, detail="No sentiment analysis data found"
            )

        return SentimentStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve sentiment statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve sentiment statistics: {str(e)}"
        )


@router.get("/journals/sentiment/batch", response_model=list[SentimentResponse])
def get_sentiments_batch_endpoint(
    journal_ids: list[int] = Query(
        ..., description="List of journal IDs to get sentiments for"
    ),
    reliable_only: bool = Query(False, description="Include only reliable predictions"),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis for multiple journal entries"""

    try:
        sentiments = get_sentiments_by_journal_ids(
            db=db, journal_ids=journal_ids, reliable_only=reliable_only
        )

        return sentiments
    except Exception as e:
        logger.error(f"Failed to retrieve batch sentiments: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve batch sentiments: {str(e)}"
        )


@router.get("/journals/sentiment/recent", response_model=list[SentimentResponse])
def get_recent_sentiments_endpoint(
    limit: int = Query(
        10, description="Number of recent sentiments to retrieve", ge=1, le=100
    ),
    reliable_only: bool = Query(True, description="Include only reliable predictions"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """Get most recent sentiment analyses"""

    try:
        sentiments = get_recent_sentiments(
            db=db, limit=limit, reliable_only=reliable_only, user_id=user_id
        )

        return sentiments
    except Exception as e:
        logger.error(f"Failed to retrieve recent sentiments: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve recent sentiments: {str(e)}"
        )
