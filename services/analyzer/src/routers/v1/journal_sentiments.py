import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.crud import journal_sentiments as sentiment_crud
from src.dependencies import get_db, get_sentiment_client
from src.ml.sentiment_client import SentimentClient
from src.schemas.sentiments import (
    SentimentAnalysisRequest,
    SentimentResponse,
    SentimentStatsResponse,
    SentimentTrendResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sentiment/analyze", response_model=SentimentResponse)
def analyze_journal_sentiment(
    request: SentimentAnalysisRequest,
    sentiment_client: SentimentClient = Depends(get_sentiment_client),
    db: Session = Depends(get_db),
):
    """Analyze sentiment for a journal entry and store the result"""
    # Load the ML model
    sentiment_client.load_model()

    # Run sentiment analysis
    try:
        analysis_result = sentiment_client.predict_sentiment(request.text)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sentiment analysis failed: {str(e)}"
        )

    # Create or update database record using CRUD
    try:
        sentiment_record = sentiment_crud.create_or_update_sentiment(
            db=db,
            journal_id=request.journal_id,
            sentiment_data=analysis_result,
            force_update=request.force_reanalyze,
        )
        return sentiment_record
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database operation failed: {str(e)}"
        )


@router.get("/{journal_id}/sentiment", response_model=SentimentResponse | None)
def get_journal_sentiment(
    journal_id: int,
    model_version: str | None = Query(
        None, description="Specific model version, defaults to latest"
    ),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis for a specific journal entry"""
    try:
        sentiment = sentiment_crud.get_sentiment_by_journal_id(
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
        raise HTTPException(
            status_code=500, detail=f"Database operation failed: {str(e)}"
        )


@router.get("/sentiment/trends", response_model=list[SentimentTrendResponse])
def get_sentiment_trends(
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
        trends_data = sentiment_crud.get_sentiment_trends(
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
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve sentiment trends: {str(e)}"
        )


@router.get("/sentiment/stats", response_model=SentimentStatsResponse)
def get_sentiment_stats(
    user_id: int | None = Query(None, description="Filter by user ID"),
    days_back: int | None = Query(None, description="Number of days to analyze", ge=1),
    db: Session = Depends(get_db),
):
    """Get overall sentiment analysis statistics"""
    try:
        stats = sentiment_crud.get_sentiment_stats(
            db=db, days_back=days_back, user_id=user_id
        )

        if stats["total_analyzed"] == 0:
            raise HTTPException(
                status_code=404, detail="No sentiment analysis data found"
            )

        return SentimentStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve sentiment statistics: {str(e)}"
        )


@router.put("/{journal_id}/sentiment", response_model=SentimentResponse)
def update_journal_sentiment(
    journal_id: int,
    sentiment_text: str,
    sentiment_client: SentimentClient = Depends(get_sentiment_client),
    db: Session = Depends(get_db),
):
    """Re-analyze and update sentiment for a journal entry"""

    request = SentimentAnalysisRequest(
        journal_id=journal_id, text=sentiment_text, force_reanalyze=True
    )

    return analyze_journal_sentiment(request, sentiment_client, db)


@router.get("/sentiment/batch", response_model=list[SentimentResponse])
def get_sentiments_batch(
    journal_ids: list[int] = Query(
        ..., description="List of journal IDs to get sentiments for"
    ),
    reliable_only: bool = Query(False, description="Include only reliable predictions"),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis for multiple journal entries"""

    try:
        sentiments = sentiment_crud.get_sentiments_by_journal_ids(
            db=db, journal_ids=journal_ids, reliable_only=reliable_only
        )

        return sentiments
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve batch sentiments: {str(e)}"
        )


@router.get("/sentiment/recent", response_model=list[SentimentResponse])
def get_recent_sentiments(
    limit: int = Query(
        10, description="Number of recent sentiments to retrieve", ge=1, le=100
    ),
    reliable_only: bool = Query(True, description="Include only reliable predictions"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """Get most recent sentiment analyses"""

    try:
        sentiments = sentiment_crud.get_recent_sentiments(
            db=db, limit=limit, reliable_only=reliable_only, user_id=user_id
        )

        return sentiments
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve recent sentiments: {str(e)}"
        )
