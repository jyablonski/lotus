from datetime import datetime

from pydantic import BaseModel, Field


class SentimentAnalysisRequest(BaseModel):
    """Request to analyze sentiment for a stored journal entry (ID-only approach)"""

    force_reanalyze: bool = Field(
        default=False,
        description="Force re-analysis even if sentiment exists for this journal",
    )


class SentimentResponse(BaseModel):
    """Response containing sentiment analysis results"""

    id: int
    journal_id: int
    sentiment: str = Field(
        description=("Sentiment classification: positive, negative, neutral, or uncertain")
    )
    confidence: float = Field(description="Model confidence score (0.0 to 1.0)")
    confidence_level: str = Field(description="Human-readable confidence: high, medium, or low")
    is_reliable: bool = Field(description="Whether the prediction meets reliability threshold")
    ml_model_version: str = Field(description="Version of the ML model used for analysis")
    created_at: datetime = Field(description="When the analysis was performed")
    all_scores: dict[str, float] | None = Field(
        default=None,
        description="Breakdown of all sentiment scores (positive, negative, neutral)",
    )

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


class SentimentTrendResponse(BaseModel):
    """Response for sentiment trends over time"""

    period: str = Field(description="Time period (YYYY-MM-DD format)")
    sentiment_counts: dict[str, int] = Field(description="Count of each sentiment in this period")
    avg_confidence: float = Field(description="Average confidence score for this period")
    total_entries: int = Field(description="Total entries analyzed in this period")
    dominant_sentiment: str = Field(description="Most common sentiment in this period")


class SentimentStatsResponse(BaseModel):
    """Response for overall sentiment statistics"""

    total_analyzed: int = Field(description="Total number of journal entries analyzed")
    reliable_count: int = Field(description="Number of reliable predictions")
    reliability_rate: float = Field(description="Percentage of reliable predictions (0.0 to 1.0)")
    sentiment_distribution: dict[str, int] = Field(description="Count of each sentiment type")
    avg_confidence: float = Field(description="Average confidence across all analyses")
    latest_model_version: str | None = Field(description="Most recent model version used")


class BulkSentimentAnalysisRequest(BaseModel):
    """Request to analyze sentiment for multiple journal entries"""

    journal_ids: list[int] = Field(description="List of journal IDs to analyze")
    force_reanalyze: bool = Field(
        default=False,
        description="Force re-analysis for all journals even if sentiment exists",
    )


class SentimentSummary(BaseModel):
    """Lightweight sentiment summary (without full details)"""

    journal_id: int
    sentiment: str
    confidence: float
    is_reliable: bool
    created_at: datetime


class SentimentDeleteResponse(BaseModel):
    """Response for sentiment deletion operations"""

    message: str
    journal_id: int
    deleted_count: int


class SentimentHealthResponse(BaseModel):
    """Response for sentiment analysis system health check"""

    model_loaded: bool
    model_version: str | None
    model_name: str
    last_analysis: datetime | None = None
    total_analyses_today: int = 0
