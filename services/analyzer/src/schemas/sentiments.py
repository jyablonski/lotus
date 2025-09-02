from datetime import datetime

from pydantic import BaseModel, Field


class SentimentAnalysisRequest(BaseModel):
    journal_id: int
    text: str
    force_reanalyze: bool = Field(
        default=False, description="Force re-analysis even if sentiment exists"
    )


class SentimentResponse(BaseModel):
    id: int
    journal_id: int
    sentiment: str
    confidence: float
    confidence_level: str
    is_reliable: bool
    ml_model_version: str
    created_at: datetime
    all_scores: dict[str, float] | None = None


class SentimentTrendResponse(BaseModel):
    period: str
    sentiment_counts: dict[str, int]
    avg_confidence: float
    total_entries: int
    dominant_sentiment: str


class SentimentStatsResponse(BaseModel):
    total_analyzed: int
    reliable_count: int
    reliability_rate: float
    sentiment_distribution: dict[str, int]
    avg_confidence: float
    latest_model_version: str
